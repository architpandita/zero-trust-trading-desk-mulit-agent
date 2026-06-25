"""
conftest.py — Shared test fixtures for the Zero-Trust Trading Desk.
Provides helpers and common signal/proposal factories used across all test phases.
"""
import pytest
import hashlib
import json

def make_analysis_signal(sender: str, signal: str, ticker: str = "AAPL"):
    from agents.execution.schemas import AnalysisSignal
    return AnalysisSignal(
        session_id="shared-fixture-session",
        sender=sender,
        ticker=ticker,
        signal=signal,
        confidence_score=0.85,
        supporting_metrics={"pe_ratio": 28.4},
        data_hash="a" * 64,
        fetched_at_utc="2026-06-25T00:00:00Z",
    )

def make_trade_proposal(ticker: str = "AAPL", value: float = 750.0, quantity: int = 5):
    from agents.execution.schemas import TradeProposal, DataProvenance
    payload = {"ticker": ticker, "close": value / quantity}
    dh = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    ).hexdigest()
    return TradeProposal(
        session_id="shared-fixture-session",
        ticker=ticker,
        action="BUY",
        quantity=quantity,
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
