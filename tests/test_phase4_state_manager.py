import pytest
from fastapi.testclient import TestClient
from api.state_manager.main import app

client = TestClient(app)

class TestStateManagerAPI:

    def test_pending_list_initially_empty(self):
        """P4-B1: No pending trades on fresh start."""
        response = client.get("/api/v1/pending")
        assert response.status_code == 200
        assert response.json() == []

    def test_approve_decision_updates_state(self):
        """P4-B3: Approve must change decision_code to APPROVED_HITL."""
        session_id = "test-hitl-session-001"
        client.post("/api/v1/pending", json={"session_id": session_id,
                                              "proposal_summary": {"ticker": "MSFT"}})
        response = client.post(f"/api/v1/decision/{session_id}",
                               json={"action": "APPROVE"})
        assert response.status_code == 200
        assert response.json()["decision_code"] == "APPROVED_HITL"

    def test_deny_decision_updates_state(self):
        """P4-B4: Deny must change decision_code to DENIED_HITL."""
        session_id = "test-hitl-session-002"
        client.post("/api/v1/pending", json={"session_id": session_id,
                                              "proposal_summary": {"ticker": "AAPL"}})
        response = client.post(f"/api/v1/decision/{session_id}",
                               json={"action": "DENY"})
        assert response.json()["decision_code"] == "DENIED_HITL"

    def test_audit_returns_recent_logs(self):
        """P4-B5: Audit endpoint returns list, max 50 entries."""
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        logs = response.json()
        assert isinstance(logs, list)
        assert len(logs) <= 50

    def test_health_endpoint_returns_score(self):
        """P4-B6: Health score must include s_safety, r_hygiene, e_delib."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        health = response.json()
        assert "s_safety" in health
        assert "r_hygiene" in health
        assert "e_delib" in health
        assert "composite_score" in health

class TestTelemetryLogger:

    @pytest.mark.asyncio
    async def test_event_log_contains_no_pii(self):
        """P4-B7: Telemetry must not log raw prompts, balances, or credentials."""
        from agents.execution.schemas import EventLog

        log = EventLog(
            log_id="test-log-001",
            session_id="test-session-001",
            event_timestamp_utc="2026-06-25T00:00:00Z",
            decision_code="EXECUTED",
            initial_prompt_hash="a" * 64,
            ticker="AAPL",
            action="BUY",
            estimated_value_usd=750.00,
            vibe_diff="AAPL shows bullish momentum above SMA50.",
            agent_latency_ms={"fundamental": 1200, "technical": 980},
            pydantic_retry_count=0,
            consensus_match=True,
            policy_checks_passed=["schema", "hash", "ticker", "asset_class", "trade_size"],
            policy_checks_failed=[],
        )

        import json
        logged_data = json.dumps(log.model_dump())
        assert "password" not in logged_data.lower()
        assert "api_key" not in logged_data.lower()
        assert "$" not in logged_data
