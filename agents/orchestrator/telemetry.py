"""
Async Telemetry Logger — P4-B7 / P4-B8
Emits EventLog records as background asyncio tasks so they never block RAM purge.
NO raw prompts, credentials, or balances are written — only hashes and codes.

OpenTelemetry spans are emitted to Phoenix (http://localhost:6006) when running.
If Phoenix is not up, tracing degrades gracefully — zero functional impact.
"""
import asyncio
import json
import logging
from agents.execution.schemas import EventLog

_logger = logging.getLogger("zero_trust.telemetry")

import os
STATE_MANAGER_URL = os.getenv("STATE_MANAGER_URL", "http://localhost:8003")

# ── OTel setup (lazy — only activates if opentelemetry is installed) ──────────
_tracer = None

def _get_tracer():
    """Return a tracer pointed at Phoenix, or None if OTel is not installed."""
    global _tracer
    if _tracer is not None:
        return _tracer
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        exporter = OTLPSpanExporter(
            endpoint="http://localhost:6006/v1/traces",
        )
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("zero_trust.orchestrator")
        _logger.info("OTel tracer initialised → Phoenix at http://localhost:6006")
    except Exception:
        _tracer = None   # OTel not installed or Phoenix not reachable — degrade silently
    return _tracer


# Fields that are safe to log (allow-list to prevent PII leakage)
_SAFE_FIELDS = {
    "log_id", "session_id", "event_timestamp_utc", "decision_code",
    "initial_prompt_hash",          # Hash only — NOT the plaintext prompt
    "ticker", "action", "estimated_value_usd",
    "agent_latency_ms", "pydantic_retry_count",
    "consensus_match", "policy_checks_passed", "policy_checks_failed",
}


def _strip_pii(log: EventLog) -> dict:
    """Return an allow-listed dict — vibe_diff and raw session data are excluded."""
    raw = log.model_dump()
    return {k: v for k, v in raw.items() if k in _SAFE_FIELDS}


def _emit_otel_span(safe: dict) -> None:
    """Emit one OTel span with EventLog fields as attributes."""
    tracer = _get_tracer()
    if tracer is None:
        return
    try:
        from opentelemetry import trace as otrace
        from opentelemetry.trace import StatusCode

        decision = safe.get("decision_code", "UNKNOWN")
        is_error = decision.startswith("REJECTED") or decision == "SCHEMA_ABORT"

        with tracer.start_as_current_span(
            f"trade.decision.{decision}",
            kind=otrace.SpanKind.INTERNAL,
        ) as span:
            # Core trade attributes
            span.set_attribute("trade.session_id",       safe.get("session_id", ""))
            span.set_attribute("trade.decision_code",    decision)
            span.set_attribute("trade.ticker",           safe.get("ticker", "N/A"))
            span.set_attribute("trade.action",           safe.get("action", "N/A"))
            span.set_attribute("trade.value_usd",        safe.get("estimated_value_usd", 0.0))
            span.set_attribute("trade.consensus_match",  safe.get("consensus_match", False))
            span.set_attribute("trade.pydantic_retries", safe.get("pydantic_retry_count", 0))
            span.set_attribute("trade.prompt_hash",      safe.get("initial_prompt_hash", ""))

            # Policy pass/fail lists (comma-joined for OTel compat)
            span.set_attribute("policy.passed", ",".join(safe.get("policy_checks_passed", [])))
            span.set_attribute("policy.failed", ",".join(safe.get("policy_checks_failed", [])))

            if is_error:
                span.set_status(StatusCode.ERROR, description=decision)
            else:
                span.set_status(StatusCode.OK)
    except Exception:
        pass  # Never let tracing break the trading pipeline


async def _write_log(log: EventLog) -> None:
    """Actual write — runs as a background task, never awaited by caller."""
    safe = _strip_pii(log)
    _logger.info(json.dumps(safe))

    # Push to state manager audit store (in-memory + JSONL) via HTTP API
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{STATE_MANAGER_URL}/api/v1/audit",
                json=safe,
                timeout=5.0
            )
    except Exception as e:
        _logger.warning(f"Telemetry failed to push audit to State Manager: {e}")

    # Emit OTel span → Phoenix (non-blocking, best-effort)
    _emit_otel_span(safe)


async def emit_event_log(log: EventLog) -> None:
    """
    P4-B8: Fire-and-forget. Returns immediately so the orchestrator's
    `finally` block can purge session_data without waiting for I/O.
    """
    asyncio.create_task(_write_log(log))
