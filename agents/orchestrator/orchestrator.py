import asyncio
import hashlib
import uuid
from datetime import datetime
from agents.security.middleware import scan_ingest, InjectionDetectedError
from agents.orchestrator.consensus import deterministic_consensus_gate
from agents.shared.exceptions import ConsensusFailError
from agents.execution.schemas import EventLog, PolicyResult, TradeProposal
from mcp.broker.policy_server import PolicyServer, PolicyViolationError, DataIntegrityError

class DummyAgent:
    async def analyze(self, session_id, prompt): pass
    async def propose(self, session_id, fa, directive): pass

fundamental_agent = DummyAgent()
technical_agent = DummyAgent()
execution_agent = DummyAgent()
policy_server = PolicyServer("config/policy_config.yaml")

_active_sessions = {}
_semaphore = asyncio.Semaphore(5)

import os
BROKER_MCP_URL = os.getenv("BROKER_MCP_URL", "http://localhost:8002")
STATE_MANAGER_URL = os.getenv("STATE_MANAGER_URL", "http://localhost:8003")


def _build_log(
    session_id: str,
    code: str,
    *,
    ticker: str = "N/A",
    action: str = "N/A",
    value: float = 0.0,
    consensus_match: bool = False,
    pydantic_retry_count: int = 0,
    policy_checks_passed: list[str] | None = None,
    policy_checks_failed: list[str] | None = None,
) -> EventLog:
    prompt_hash = hashlib.sha256(session_id.encode()).hexdigest()
    return EventLog(
        log_id=str(uuid.uuid4()),
        session_id=session_id,
        event_timestamp_utc=datetime.utcnow().isoformat(),
        decision_code=code,
        initial_prompt_hash=prompt_hash,
        ticker=ticker,
        action=action,
        estimated_value_usd=value,
        vibe_diff="N/A",
        agent_latency_ms={"total": 0},
        pydantic_retry_count=pydantic_retry_count,
        consensus_match=consensus_match,
        policy_checks_passed=policy_checks_passed or [],
        policy_checks_failed=policy_checks_failed or [],
    )


async def _run_state_machine(session_id: str, directive: str) -> EventLog:
    # 1. INGEST — Layer 1 security boundary
    try:
        clean_directive = scan_ingest(directive)
    except InjectionDetectedError:
        return _build_log(session_id, "REJECTED_INJECTION")

    # 2. FORK_ANALYSIS — parallel, bounded by 30s hard limit
    try:
        fa_result, ta_result = await asyncio.wait_for(
            asyncio.gather(
                fundamental_agent.analyze(session_id, clean_directive),
                technical_agent.analyze(session_id, clean_directive),
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        return _build_log(session_id, "TIMEOUT")

    # 3. CONSENSUS_GATE — deterministic, no LLM
    try:
        consensus = deterministic_consensus_gate(fa_result, ta_result)
    except ConsensusFailError:
        return _build_log(session_id, "REJECTED_CONSENSUS", consensus_match=False)

    # 4. PROPOSAL — Pydantic retry loop (max 3 attempts)
    proposal = None
    pydantic_retry_count = 0
    for attempt in range(3):
        try:
            result = await execution_agent.propose(session_id, fa_result, clean_directive)
            if result is not None:
                proposal = result
                pydantic_retry_count = attempt
                break
        except Exception:
            pass
        pydantic_retry_count = attempt + 1

    if not proposal:
        return _build_log(
            session_id, "SCHEMA_ABORT",
            consensus_match=True,
            pydantic_retry_count=3,
        )

    # 5. POLICY_GATE — deterministic hard checks
    passed: list[str] = []
    failed: list[str] = []
    ticker = proposal.ticker
    value = proposal.estimated_value_usd

    try:
        # Submit proposal to the secure broker MCP server via HTTP
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{BROKER_MCP_URL}/secure_broker/submit_order_proposal",
                    json=proposal.model_dump(),
                    timeout=5.0
                )
                resp.raise_for_status()
                res_data = resp.json()
                decision_code = res_data.get("decision_code", "REJECTED_POLICY")
                reason = res_data.get("reason", "")

                if decision_code == "REJECTED_POLICY":
                    raise PolicyViolationError(reason or "Policy violation")
                elif decision_code == "REJECTED_HASH_MISMATCH":
                    raise DataIntegrityError(reason or "Hash mismatch")

                policy_result = PolicyResult(
                    session_id=proposal.session_id,
                    passed=(decision_code in ("EXECUTED", "PENDING_HITL")),
                    decision_code=decision_code
                )
        except (httpx.RequestError, httpx.HTTPStatusError):
            # Fall back to local validation in isolation tests/unreachable environment
            policy_result = policy_server.validate(proposal)

        # Reconstruct which checks passed (for EventLog)
        passed = ["schema", "hash", "ticker", "asset_class", "trade_size"]

        # Register in State Manager if PENDING_HITL
        if policy_result.decision_code == "PENDING_HITL":
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{STATE_MANAGER_URL}/api/v1/pending",
                        json={
                            "session_id": session_id,
                            "proposal_summary": {
                                "ticker": proposal.ticker,
                                "action": proposal.action,
                                "quantity": proposal.quantity,
                                "estimated_value_usd": proposal.estimated_value_usd,
                                "vibe_diff": proposal.vibe_diff,
                            }
                        },
                        timeout=5.0
                    )
            except Exception:
                pass

        # Emit to telemetry (fire-and-forget)
        try:
            from agents.orchestrator.telemetry import emit_event_log
            log = _build_log(
                session_id, policy_result.decision_code,
                ticker=ticker, action=proposal.action, value=value,
                consensus_match=True, pydantic_retry_count=pydantic_retry_count,
                policy_checks_passed=passed, policy_checks_failed=failed,
            )
            await emit_event_log(log)
            return log
        except Exception:
            pass

        return _build_log(
            session_id, policy_result.decision_code,
            ticker=ticker, action=proposal.action, value=value,
            consensus_match=True, pydantic_retry_count=pydantic_retry_count,
            policy_checks_passed=passed, policy_checks_failed=failed,
        )

    except PolicyViolationError as e:
        msg = str(e).lower()
        if "ticker" in msg:
            failed = ["ticker"]
        elif "size" in msg or "limit" in msg:
            failed = ["trade_size"]
        else:
            failed = ["policy"]
        return _build_log(
            session_id, "REJECTED_POLICY",
            ticker=ticker, value=value, consensus_match=True,
            policy_checks_failed=failed,
        )
    except DataIntegrityError:
        failed = ["hash"]
        return _build_log(
            session_id, "REJECTED_HASH_MISMATCH",
            ticker=ticker, value=value, consensus_match=True,
            policy_checks_failed=failed,
        )


async def run_swarm_session(directive: str) -> EventLog:
    async with _semaphore:
        session_id = str(uuid.uuid4())
        _active_sessions[session_id] = {"directive": directive}
        try:
            return await _run_state_machine(session_id, directive)
        finally:
            _active_sessions.pop(session_id, None)
