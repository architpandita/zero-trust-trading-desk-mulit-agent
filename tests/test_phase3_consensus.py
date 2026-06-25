import pytest
from agents.orchestrator.consensus import deterministic_consensus_gate
from agents.shared.exceptions import ConsensusFailError
from agents.execution.schemas import AnalysisSignal

def make_signal(sender: str, signal: str) -> AnalysisSignal:
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

class TestDeterministicConsensusGate:

    def test_matching_bullish_signals_agree(self):
        """P3-B1: Two BULLISH signals produce consensus_match=True."""
        fa = make_signal("fundamental_agent", "BULLISH")
        ta = make_signal("technical_agent", "BULLISH")
        result = deterministic_consensus_gate(fa, ta)
        assert result.consensus_match is True
        assert result.signal == "BULLISH"

    def test_matching_bearish_signals_agree(self):
        """P3-B1: Two BEARISH signals also produce consensus."""
        fa = make_signal("fundamental_agent", "BEARISH")
        ta = make_signal("technical_agent", "BEARISH")
        result = deterministic_consensus_gate(fa, ta)
        assert result.consensus_match is True

    def test_conflicting_signals_raise_error(self):
        """P3-B2: Fail-Closed — conflicting signals must never proceed to execution."""
        fa = make_signal("fundamental_agent", "BULLISH")
        ta = make_signal("technical_agent", "BEARISH")
        with pytest.raises(ConsensusFailError):
            deterministic_consensus_gate(fa, ta)
