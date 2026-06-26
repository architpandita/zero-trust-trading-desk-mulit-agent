"""
Scenario-aware agents for Golden Dataset eval tests.
These agents inspect the directive string and return pre-canned responses
so the eval pipeline validates orchestrator logic — not LLM output.
"""
import asyncio
import hashlib
import json
from agents.execution.schemas import AnalysisSignal, TradeProposal, DataProvenance


def _make_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()


def _get_orig_directive(session_id: str, default: str) -> str:
    try:
        from agents.orchestrator.orchestrator import _active_sessions
        return _active_sessions.get(session_id, {}).get("directive", default)
    except Exception:
        return default


class ScenarioFundamentalAgent:
    async def analyze(self, session_id: str, directive: str) -> AnalysisSignal:
        orig_directive = _get_orig_directive(session_id, directive)
        directive_lower = orig_directive.lower()
        # Special directive keywords drive signal
        if "force_timeout" in directive_lower:
            await asyncio.sleep(35)
        if "fundamental: bearish" in directive_lower or "fa=bullish, ta=bearish" in directive_lower:
            signal = "BEARISH"
        else:
            signal = "BULLISH"
        ticker = _extract_ticker(orig_directive)
        return AnalysisSignal(
            session_id=session_id,
            sender="fundamental_agent",
            ticker=ticker,
            signal=signal,
            confidence_score=0.85,
            supporting_metrics={"pe_ratio": 28.4},
            data_hash="a" * 64,
            fetched_at_utc="2026-06-25T00:00:00Z",
        )


class ScenarioTechnicalAgent:
    async def analyze(self, session_id: str, directive: str) -> AnalysisSignal:
        orig_directive = _get_orig_directive(session_id, directive)
        directive_lower = orig_directive.lower()
        if "force_timeout" in directive_lower:
            await asyncio.sleep(35)
        if "technical: bearish" in directive_lower or "ta=bearish" in directive_lower.replace(" ", ""):
            signal = "BEARISH"
        else:
            signal = "BULLISH"
        ticker = _extract_ticker(orig_directive)
        return AnalysisSignal(
            session_id=session_id,
            sender="technical_agent",
            ticker=ticker,
            signal=signal,
            confidence_score=0.80,
            supporting_metrics={"rsi": 55.0},
            data_hash="b" * 64,
            fetched_at_utc="2026-06-25T00:00:00Z",
        )


class ScenarioExecutionAgent:
    async def propose(self, session_id: str, fa: AnalysisSignal, directive: str) -> TradeProposal | None:
        orig_directive = _get_orig_directive(session_id, directive)
        directive_lower = orig_directive.lower()
        # Force schema failure scenario
        if "force_schema_failure" in directive_lower:
            return None   # Simulates retry failure — returns None 3 times

        ticker = fa.ticker
        value = _extract_value(orig_directive)
        qty = max(1, int(value / 150))
        payload = {"ticker": ticker, "close": value / qty}
        dh = _make_hash(payload)
        return TradeProposal(
            session_id=session_id,
            ticker=ticker,
            action="BUY",
            quantity=qty,
            estimated_value_usd=value,
            vibe_diff=f"{ticker} shows strong fundamentals with bullish momentum confirmed.",
            data_hash=dh,
            provenance=[DataProvenance(
                mcp_tool="market_data/fetch_candles",
                endpoint_url="http://localhost:8001/market_data/fetch_candles",
                response_sha256=dh,
                fetched_at_utc="2026-06-25T00:00:00Z"
            )]
        )


def _extract_ticker(directive: str) -> str:
    for ticker in ["MSFT", "AAPL", "SPY", "QQQ", "BTC"]:
        if ticker.lower() in directive.lower():
            return ticker
    return "AAPL"


def _extract_value(directive: str) -> float:
    import re
    # Find all standalone numbers (not ticker symbols) and pick the largest
    matches = re.findall(r"\b(\d[\d,]*(?:\.\d+)?)\b", directive)
    if matches:
        values = [float(m.replace(",", "")) for m in matches]
        # The trade value is almost always the largest number in the directive
        largest = max(values)
        if largest >= 100:
            return largest
    return 750.0
