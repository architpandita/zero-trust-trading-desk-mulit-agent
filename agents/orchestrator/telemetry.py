"""
Async Telemetry Logger — P4-B7 / P4-B8
Emits EventLog records as background asyncio tasks so they never block RAM purge.
NO raw prompts, credentials, or balances are written — only hashes and codes.
"""
import asyncio
import json
import logging
from agents.execution.schemas import EventLog

_logger = logging.getLogger("zero_trust.telemetry")

# Fields that are safe to log (allow-list to prevent PII leakage)
_SAFE_FIELDS = {
    "log_id", "session_id", "event_timestamp_utc", "decision_code",
    "initial_prompt_hash",          # Hash only — NOT the plaintext prompt
    "ticker", "action", "estimated_value_usd",
    "agent_latency_ms", "pydantic_retry_count",
    "consensus_match", "policy_checks_passed", "policy_checks_failed",
}


def _strip_pii(log: EventLog) -> dict:
    """Return an allow-listed dict — vibe_diff and raw session data are excluded."""
    raw = log.model_dump()
    return {k: v for k, v in raw.items() if k in _SAFE_FIELDS}


async def _write_log(log: EventLog) -> None:
    """Actual write — runs as a background task, never awaited by caller."""
    safe = _strip_pii(log)
    _logger.info(json.dumps(safe))

    # Also push to state manager audit store
    try:
        from api.state_manager.audit import async_push_audit
        await async_push_audit(safe)
    except ImportError:
        pass  # Degrade gracefully in test isolation


async def emit_event_log(log: EventLog) -> None:
    """
    P4-B8: Fire-and-forget. Returns immediately so the orchestrator's
    `finally` block can purge session_data without waiting for I/O.
    """
    asyncio.create_task(_write_log(log))
