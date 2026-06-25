from fastapi import FastAPI, HTTPException
from api.state_manager.models import PendingEntry, HITLDecision, DecisionResponse, AuditEntry
from api.state_manager.audit import push_audit, get_recent_audit, compute_health_score

app = FastAPI(title="Zero-Trust State Manager", version="1.0.0")

# In-process ephemeral store: session_id -> PendingEntry
# Designed to be wiped on restart — no persistence of trade state.
_pending: dict[str, PendingEntry] = {}


@app.get("/api/v1/pending")
def list_pending() -> list[dict]:
    """P4-B1/B2: Return all currently pending HITL trades."""
    return [entry.model_dump() for entry in _pending.values()]


@app.post("/api/v1/pending", status_code=201)
def register_pending(entry: PendingEntry) -> dict:
    """Internal endpoint — orchestrator posts here when policy routes to PENDING_HITL."""
    _pending[entry.session_id] = entry
    push_audit({
        "session_id": entry.session_id,
        "decision_code": "PENDING_HITL",
        "proposal_summary": entry.proposal_summary,
        "consensus_match": False,
    })
    return {"registered": entry.session_id}


@app.post("/api/v1/decision/{session_id}")
def record_decision(session_id: str, decision: HITLDecision) -> DecisionResponse:
    """P4-B3/B4: Human approves or denies a pending trade."""
    if session_id not in _pending:
        raise HTTPException(status_code=404, detail="Pending trade not found")

    code = "APPROVED_HITL" if decision.action == "APPROVE" else "DENIED_HITL"
    entry = _pending.pop(session_id)
    push_audit({
        "session_id": session_id,
        "decision_code": code,
        "proposal_summary": entry.proposal_summary,
        "consensus_match": True,
    })
    return DecisionResponse(session_id=session_id, decision_code=code)


@app.get("/api/v1/audit")
def get_audit() -> list[dict]:
    """P4-B5: Return last 50 EventLog entries (no PII — hashes only)."""
    return get_recent_audit(50)


@app.get("/api/v1/health")
def health_check() -> dict:
    """P4-B6: Compute and return the System Health Score."""
    return compute_health_score().model_dump()
