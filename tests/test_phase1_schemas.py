import pytest
from pydantic import ValidationError
from agents.execution.schemas import TradeProposal, DataProvenance

VALID_PROVENANCE = [DataProvenance(
    mcp_tool="market_data/fetch_candles",
    endpoint_url="http://mcp-market-data:8001/market_data/fetch_candles",
    response_sha256="a" * 64,
    fetched_at_utc="2026-06-25T00:00:00Z"
)]

VALID_PROPOSAL = dict(
    session_id="550e8400-e29b-41d4-a716-446655440000",
    ticker="AAPL",
    action="BUY",
    quantity=10,
    estimated_value_usd=750.00,
    vibe_diff="AAPL shows strong fundamentals and bullish momentum above 50-day SMA.",
    data_hash="b" * 64,
    provenance=VALID_PROVENANCE,
)

class TestTradeProposalSchema:

    def test_valid_proposal_parses(self):
        """P1-B4: Well-formed proposal must parse without error."""
        proposal = TradeProposal(**VALID_PROPOSAL)
        assert proposal.ticker == "AAPL"
        assert proposal.action == "BUY"

    def test_lowercase_ticker_rejected(self):
        """P1-B5: Ticker must be uppercase 1–5 chars."""
        bad = {**VALID_PROPOSAL, "ticker": "aapl"}
        with pytest.raises(ValidationError):
            TradeProposal(**bad)

    def test_missing_data_hash_rejected(self):
        """P1-B6: data_hash is required — no hash means no provenance proof."""
        bad = {k: v for k, v in VALID_PROPOSAL.items() if k != "data_hash"}
        with pytest.raises(ValidationError):
            TradeProposal(**bad)

    def test_missing_provenance_rejected(self):
        """P1-B6: provenance list must have at least 1 entry."""
        bad = {**VALID_PROPOSAL, "provenance": []}
        with pytest.raises(ValidationError):
            TradeProposal(**bad)

    def test_short_vibe_diff_rejected(self):
        """P1-B6: vibe_diff < 20 chars is rejected."""
        bad = {**VALID_PROPOSAL, "vibe_diff": "Too short"}
        with pytest.raises(ValidationError):
            TradeProposal(**bad)

    def test_hold_is_valid_action(self):
        """P1-B4: HOLD is a valid action alongside BUY and SELL."""
        proposal = TradeProposal(**{**VALID_PROPOSAL, "action": "HOLD"})
        assert proposal.action == "HOLD"

    def test_invalid_action_rejected(self):
        """P1-B5: Arbitrary action strings are not allowed."""
        with pytest.raises(ValidationError):
            TradeProposal(**{**VALID_PROPOSAL, "action": "YOLO"})
