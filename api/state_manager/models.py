from pydantic import BaseModel
from typing import Optional, Literal

class PendingEntry(BaseModel):
    session_id: str
    proposal_summary: dict
    decision_code: str = "PENDING_HITL"

class HITLDecision(BaseModel):
    action: Literal["APPROVE", "DENY"]

class DecisionResponse(BaseModel):
    session_id: str
    decision_code: str

class AuditEntry(BaseModel):
    session_id: str
    decision_code: str
    ticker: Optional[str] = None
    estimated_value_usd: Optional[float] = None

class HealthScore(BaseModel):
    s_safety: float     # Security & injection rejection rate
    r_hygiene: float    # Context hygiene / PII masking rate
    e_delib: float      # Deliberation / consensus hit rate
    composite_score: float
    status: str
