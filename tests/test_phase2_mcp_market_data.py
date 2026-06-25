import hashlib, json
import pytest
from fastapi.testclient import TestClient
from mcp.market_data.main import app

client = TestClient(app)

class TestMCPMarketDataServer:

    def test_fetch_financials_returns_hash(self):
        """P2-B1: Every response must include a data_hash field."""
        response = client.get("/market_data/fetch_financials", params={"ticker": "AAPL"})
        assert response.status_code == 200
        body = response.json()
        assert "data_hash" in body
        assert len(body["data_hash"]) == 64  # SHA256 hex = 64 chars

    def test_fetch_financials_hash_is_deterministic(self):
        """P2-B2: Same request must produce same hash (deterministic payload)."""
        r1 = client.get("/market_data/fetch_financials", params={"ticker": "AAPL"})
        r2 = client.get("/market_data/fetch_financials", params={"ticker": "AAPL"})
        assert r1.json()["data_hash"] == r2.json()["data_hash"]

    def test_fetch_candles_hash_matches_body(self):
        """P2-B2: data_hash must equal SHA256 of the response body (excl. hash field)."""
        response = client.get("/market_data/fetch_candles", params={"ticker": "AAPL", "period": "1mo"})
        body = response.json()
        returned_hash = body.pop("data_hash")
        canonical = json.dumps(body, sort_keys=True, separators=(',', ':'))
        recalculated = hashlib.sha256(canonical.encode()).hexdigest()
        assert returned_hash == recalculated

    def test_unknown_ticker_returns_404(self):
        """P2-B3: Unsupported tickers must not silently return empty data."""
        response = client.get("/market_data/fetch_candles", params={"ticker": "FAKECORP", "period": "1mo"})
        assert response.status_code == 404
