import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from agents.orchestrator.orchestrator import run_swarm_session
from agents.shared.exceptions import ConsensusFailError
from agents.execution.schemas import AnalysisSignal, PolicyResult, EventLog

def _make_signal(sender: str, signal: str) -> AnalysisSignal:
    return AnalysisSignal(
        session_id="test-session-001",
        sender=sender,
        ticker="AAPL",
        signal=signal,
        confidence_score=0.85,
        supporting_metrics={"pe_ratio": 28.4},
        data_hash="a" * 64,
        fetched_at_utc="2026-06-25T00:00:00Z",
    )

def _make_bullish_signal(sender: str) -> AnalysisSignal:
    return _make_signal(sender, "BULLISH")

def _make_policy_result(code: str) -> PolicyResult:
    return PolicyResult(
        session_id="test-session-001",
        passed=(code == "EXECUTED"),
        decision_code=code
    )

class TestOrchestratorStateMachine:

    @pytest.mark.asyncio
    async def test_successful_session_returns_executed(self):
        """P3-B3: Happy path — matching signals produce EXECUTED EventLog."""
        with patch("agents.orchestrator.orchestrator.fundamental_agent.analyze",
                   new_callable=AsyncMock) as fa_mock, \
             patch("agents.orchestrator.orchestrator.technical_agent.analyze",
                   new_callable=AsyncMock) as ta_mock, \
             patch("agents.orchestrator.orchestrator.execution_agent.propose",
                   new_callable=AsyncMock) as exec_mock, \
             patch("agents.orchestrator.orchestrator.policy_server.validate") as ps_mock:

            fa_mock.return_value = _make_bullish_signal("fundamental_agent")
            ta_mock.return_value = _make_bullish_signal("technical_agent")
            
            from agents.execution.schemas import TradeProposal
            from tests.test_phase2_mcp_broker import _make_valid_proposal_dict
            exec_mock.return_value = TradeProposal(**_make_valid_proposal_dict(750.0))

            ps_mock.return_value = _make_policy_result("EXECUTED")

            event_log = await run_swarm_session("Analyze AAPL")
            assert event_log.decision_code == "EXECUTED"

    @pytest.mark.asyncio
    async def test_consensus_failure_returns_rejected_consensus(self):
        """P3-B4: Conflicting signals must return REJECTED_CONSENSUS — never reach Policy Gate."""
        with patch("agents.orchestrator.orchestrator.fundamental_agent.analyze",
                   new_callable=AsyncMock) as fa_mock, \
             patch("agents.orchestrator.orchestrator.technical_agent.analyze",
                   new_callable=AsyncMock) as ta_mock:

            fa_mock.return_value = _make_signal("fundamental_agent", "BULLISH")
            ta_mock.return_value = _make_signal("technical_agent", "BEARISH")

            event_log = await run_swarm_session("Analyze MSFT")
            assert event_log.decision_code == "REJECTED_CONSENSUS"

    @pytest.mark.asyncio
    async def test_agent_timeout_returns_timeout(self):
        """P3-B5: Agents exceeding 30s wall-clock must be aborted — never hang."""
        async def slow_agent(*args, **kwargs):
            await asyncio.sleep(35)  # Exceeds 30s hard limit

        with patch("agents.orchestrator.orchestrator.fundamental_agent.analyze",
                   new=slow_agent):
            event_log = await run_swarm_session("Analyze SPY")
            assert event_log.decision_code == "TIMEOUT"

    @pytest.mark.asyncio
    async def test_session_data_purged_after_completion(self):
        """P3-B7: session_data must not persist in memory after session ends."""
        with patch("agents.orchestrator.orchestrator.fundamental_agent.analyze",
                   new_callable=AsyncMock) as fa_mock, \
             patch("agents.orchestrator.orchestrator.technical_agent.analyze",
                   new_callable=AsyncMock) as ta_mock, \
             patch("agents.orchestrator.orchestrator.execution_agent.propose",
                   new_callable=AsyncMock) as exec_mock, \
             patch("agents.orchestrator.orchestrator.policy_server.validate") as ps_mock:

            fa_mock.return_value = _make_bullish_signal("fundamental_agent")
            ta_mock.return_value = _make_bullish_signal("technical_agent")
            
            from agents.execution.schemas import TradeProposal
            from tests.test_phase2_mcp_broker import _make_valid_proposal_dict
            exec_mock.return_value = TradeProposal(**_make_valid_proposal_dict(750.0))
            
            ps_mock.return_value = _make_policy_result("EXECUTED")

            import agents.orchestrator.orchestrator as orch
            sessions_before = len(orch._active_sessions)
            await run_swarm_session("Analyze QQQ")
            sessions_after = len(orch._active_sessions)

            assert sessions_after == sessions_before  # Session cleaned up

    @pytest.mark.asyncio
    async def test_semaphore_blocks_concurrent_sessions(self):
        """P3-B8: asyncio.Semaphore(5) blocks a 6th concurrent session."""
        import agents.orchestrator.orchestrator as orch
        from agents.orchestrator.orchestrator import _build_log
        
        orch._semaphore = asyncio.Semaphore(5)
        
        async def mock_state_machine(session_id, directive):
            await asyncio.sleep(0.1)
            return _build_log(session_id, "EXECUTED")
            
        with patch("agents.orchestrator.orchestrator._run_state_machine", new=mock_state_machine):
            tasks = [asyncio.create_task(run_swarm_session(f"Task {i}")) for i in range(6)]
            
            await asyncio.sleep(0.05)
            assert len(orch._active_sessions) == 5
            
            await asyncio.gather(*tasks)
            assert len(orch._active_sessions) == 0
