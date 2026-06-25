from fastapi import HTTPException

ALLOWED_TICKERS = ["AAPL", "MSFT", "SPY", "QQQ"]

def fetch_financials(ticker: str) -> dict:
    if ticker.upper() not in ALLOWED_TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return {
        "ticker": ticker.upper(),
        "pe_ratio": 25.5,
        "market_cap": 2500000000000
    }

def fetch_candles(ticker: str, period: str) -> dict:
    if ticker.upper() not in ALLOWED_TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return {
        "ticker": ticker.upper(),
        "period": period,
        "close": 150.00,
        "volume": 1000000
    }
