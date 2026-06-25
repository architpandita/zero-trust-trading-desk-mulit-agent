from pydantic import BaseModel, Field, field_validator
from typing import Literal

class DataProvenance(BaseModel):
    mcp_tool: str
    endpoint_url: str
    response_sha256: str = Field(min_length=64)
    fetched_at_utc: str

class TradeProposal(BaseModel):
    session_id: str = Field(description="UUID v4 — links to A2A blackboard session")
    ticker: str
    action: Literal["BUY", "SELL", "HOLD"]
    quantity: int = Field(gt=0)
    estimated_value_usd: float = Field(gt=0.0)
    vibe_diff: str = Field(
        min_length=20,
        description="Plain-English trading thesis for HITL UI display and audit trail"
    )
    data_hash: str = Field(
        min_length=64,
        description="SHA256 of the MCP market data payload — provenance proof"
    )
    provenance: list[DataProvenance] = Field(
        min_length=1,
        description="Full citation of all MCP tool invocations used"
    )

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v.isupper() or not (1 <= len(v) <= 5):
            raise ValueError("Ticker must be uppercase, 1–5 characters.")
        return v

class AnalysisSignal(BaseModel):
    session_id: str
    sender: Literal["fundamental_agent", "technical_agent"]
    ticker: str
    signal: Literal["BULLISH", "BEARISH", "HOLD"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    supporting_metrics: dict
    data_hash: str = Field(min_length=64)
    fetched_at_utc: str

class EventLog(BaseModel):
    log_id: str
    session_id: str
    event_timestamp_utc: str
    decision_code: Literal[
        "EXECUTED",
        "REJECTED_POLICY",
        "REJECTED_CONSENSUS",
        "REJECTED_INJECTION",
        "REJECTED_HASH_MISMATCH",
        "PENDING_HITL",
        "APPROVED_HITL",
        "DENIED_HITL",
        "TIMEOUT",
        "SCHEMA_ABORT",
    ]
    initial_prompt_hash: str
    ticker: str
    action: str
    estimated_value_usd: float
    vibe_diff: str
    agent_latency_ms: dict
    pydantic_retry_count: int
    consensus_match: bool
    policy_checks_passed: list[str]
    policy_checks_failed: list[str]

class PolicyResult(BaseModel):
    session_id: str
    passed: bool
    decision_code: str
    hitl_required: bool = False
    rejection_reason: str | None = None
    broker_ack: str | None = None
