import hashlib, json
import pytest
from mcp.broker.policy_server import PolicyServer, DataIntegrityError, PolicyViolationError
from agents.execution.schemas import TradeProposal, DataProvenance

# --- Fixtures ---

RAW_PAYLOAD = {"ticker": "AAPL", "close": 150.00, "volume": 1000000}
VALID_HASH = hashlib.sha256(
    json.dumps(RAW_PAYLOAD, sort_keys=True, separators=(',', ':')).encode()
).hexdigest()

def make_proposal(**overrides) -> TradeProposal:
    base = dict(
        session_id="test-session-001",
        ticker="AAPL",
        action="BUY",
        quantity=5,
        estimated_value_usd=750.00,
        vibe_diff="AAPL shows strong fundamentals with bullish momentum confirmed.",
        data_hash=VALID_HASH,
        provenance=[DataProvenance(
            mcp_tool="market_data/fetch_candles",
            endpoint_url="http://localhost:8001/market_data/fetch_candles",
            response_sha256=VALID_HASH,
            fetched_at_utc="2026-06-25T00:00:00Z"
        )],
    )
    return TradeProposal(**{**base, **overrides})

class TestPolicyServer:

    @pytest.fixture(autouse=True)
    def server(self):
        self.ps = PolicyServer("config/policy_config.yaml")

    def test_server_loads_config(self):
        """P1-B7: PolicyServer must load the YAML config on init."""
        assert self.ps.policy["version"] == "2.0.0"
        assert "global_risk_mandate" in self.ps.policy

    def test_valid_proposal_passes(self):
        """P1-B11: A fully valid proposal ≤ $1,000 returns EXECUTED."""
        result = self.ps.validate(make_proposal())
        assert result.passed is True
        assert result.decision_code == "EXECUTED"

    def test_blocked_ticker_rejected(self):
        """P1-B8: Ticker not in allowed_tickers is hard rejected."""
        with pytest.raises(PolicyViolationError):
            self.ps.validate(make_proposal(ticker="BTC"))

    def test_oversized_trade_rejected(self):
        """P1-B9: Trade > $2,500 exceeds max_single_trade_value_usd."""
        with pytest.raises(PolicyViolationError):
            self.ps.validate(make_proposal(estimated_value_usd=3000.00))

    def test_high_value_routes_to_hitl(self):
        """P1-B10: Trade > $1,000 and ≤ $2,500 must route to PENDING_HITL."""
        result = self.ps.validate(make_proposal(estimated_value_usd=1500.00))
        assert result.hitl_required is True
        assert result.decision_code == "PENDING_HITL"

    def test_hash_mismatch_raises_integrity_error(self):
        """P1-B12: Tampered data_hash must raise DataIntegrityError."""
        with pytest.raises(DataIntegrityError):
            self.ps.validate(make_proposal(data_hash="tampered" + "0" * 56))
