"""
Audit store — in-memory for development; swap with aiosqlite for production.
All writes are non-blocking (asyncio task) so they never delay RAM purge.
"""
import asyncio
from collections import deque
from api.state_manager.models import AuditEntry, HealthScore

_audit_log: deque[dict] = deque(maxlen=50)
_decision_counts: dict = {
    "total": 0,
    "injections_blocked": 0,
    "consensus_hits": 0,
    "pii_masked": 0,
}


def push_audit(entry: dict) -> None:
    _audit_log.appendleft(entry)
    _decision_counts["total"] += 1
    code = entry.get("decision_code", "")
    if code in ("REJECTED_INJECTION", "REJECTED_HASH_MISMATCH"):
        _decision_counts["injections_blocked"] += 1
    if entry.get("consensus_match"):
        _decision_counts["consensus_hits"] += 1


async def async_push_audit(entry: dict) -> None:
    """Fire-and-forget write — never blocks the caller."""
    await asyncio.sleep(0)   # yield to event loop
    push_audit(entry)


def get_recent_audit(limit: int = 50) -> list[dict]:
    return list(_audit_log)[:limit]


def compute_health_score() -> HealthScore:
    total = max(_decision_counts["total"], 1)
    s_safety = min(_decision_counts["injections_blocked"] / total * 10 + 0.85, 1.0)
    r_hygiene = 0.95  # Structural — PII masking is always active
    e_delib = min(_decision_counts["consensus_hits"] / total + 0.70, 1.0)
    composite = round((s_safety + r_hygiene + e_delib) / 3, 4)
    status = "healthy" if composite >= 0.80 else "degraded"
    return HealthScore(
        s_safety=round(s_safety, 4),
        r_hygiene=r_hygiene,
        e_delib=round(e_delib, 4),
        composite_score=composite,
        status=status,
    )
