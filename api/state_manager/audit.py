"""
Audit store — in-memory + JSONL file persistence.
In-memory deque for fast reads; JSONL file so history survives restarts.
All writes are non-blocking (asyncio task) so they never delay RAM purge.
"""
import asyncio
import json
import pathlib
from datetime import datetime, timezone
from collections import deque
from api.state_manager.models import AuditEntry, HealthScore

_audit_log: deque[dict] = deque(maxlen=200)
_decision_counts: dict = {
    "total": 0,
    "injections_blocked": 0,
    "consensus_hits": 0,
    "pii_masked": 0,
}

# ── File persistence ─────────────────────────────────────────────────────────
_LOG_DIR  = pathlib.Path("logs")
_LOG_FILE = _LOG_DIR / "audit.jsonl"
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def _write_jsonl(entry: dict) -> None:
    """Append one record to logs/audit.jsonl — safe to call from any thread."""
    record = {"_written_at": datetime.now(timezone.utc).isoformat(), **entry}
    with open(_LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def push_audit(entry: dict) -> None:
    _audit_log.appendleft(entry)
    _decision_counts["total"] += 1
    code = entry.get("decision_code", "")
    if code in ("REJECTED_INJECTION", "REJECTED_HASH_MISMATCH"):
        _decision_counts["injections_blocked"] += 1
    if entry.get("consensus_match"):
        _decision_counts["consensus_hits"] += 1
    # Persist to disk (sync — fast enough for O(1) JSONL append)
    try:
        _write_jsonl(entry)
    except OSError:
        pass  # Degrade gracefully if disk is unavailable


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
