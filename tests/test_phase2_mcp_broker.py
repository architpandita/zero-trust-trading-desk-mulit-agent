import pytest
import re
from fastapi.testclient import TestClient

def _make_valid_proposal_dict(value: float) -> dict:
    from mcp.market_data.hash_utils import generate_data_hash
    dummy_payload = {"ticker": "AAPL", "close": 150.0}
    dh = generate_data_hash(dummy_payload)
    return dict(
        session_id="test-session-001",
        ticker="AAPL",
        action="BUY",
        quantity=max(1, int(value/150)),
        estimated_value_usd=value,
        vibe_diff="AAPL shows strong fundamentals with bullish momentum confirmed.",
        data_hash=dh,
        provenance=[dict(
            mcp_tool="market_data/fetch_candles",
            endpoint_url="http://localhost:8001/market_data/fetch_candles",
            response_sha256=dh,
            fetched_at_utc="2026-06-25T00:00:00Z"
        )]
    )

class TestMCPSecureBrokerServer:

    @pytest.fixture(autouse=True)
    def broker_client(self):
        from mcp.broker.main import app as broker_app
        self.broker = TestClient(broker_app)

    def test_valid_proposal_returns_decision_code(self):
        """P2-B4: A valid proposal must return a decision_code."""
        payload = _make_valid_proposal_dict(value=750.00)
        response = self.broker.post("/secure_broker/submit_order_proposal", json=payload)
        assert response.status_code == 200
        assert "decision_code" in response.json()

    def test_oversized_trade_returns_rejected_policy(self):
        """P2-B5: Trade > $2,500 must return REJECTED_POLICY — never reach broker."""
        payload = _make_valid_proposal_dict(value=3000.00)
        response = self.broker.post("/secure_broker/submit_order_proposal", json=payload)
        body = response.json()
        assert body["decision_code"] == "REJECTED_POLICY"

    def test_portfolio_balance_is_masked(self):
        """P2-B6: Real account balance must never be returned — only [MASKED_BALANCE]."""
        response = self.broker.get("/secure_broker/get_portfolio_balance")
        body = response.json()
        assert body["balance"] == "[MASKED_BALANCE]"
        # Ensure no real number leaks through
        assert not re.search(r"\$[\d,]+", str(body))
