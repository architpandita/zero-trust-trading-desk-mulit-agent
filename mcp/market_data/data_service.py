from fastapi import HTTPException

ALLOWED_TICKERS = [
    # Original
    "AAPL", "MSFT", "SPY", "QQQ",
    # Big Tech / Top 10 US Stocks
    "GOOGL", "AMZN", "NVDA", "META", "TSLA", "LLY", "AVGO", "BRK.B",
    # Finance
    "JPM", "BAC", "GS", "V", "MA",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV",
    # Energy
    "XOM", "CVX",
    # Industrials / ETFs
    "DIA", "IWM", "VTI",
]

# Realistic mock fundamentals per ticker
_FINANCIALS = {
    "AAPL":  {"pe_ratio": 28.5,  "market_cap": 3_000_000_000_000},
    "MSFT":  {"pe_ratio": 35.2,  "market_cap": 2_900_000_000_000},
    "SPY":   {"pe_ratio": 22.1,  "market_cap": 550_000_000_000},
    "QQQ":   {"pe_ratio": 30.4,  "market_cap": 230_000_000_000},
    "GOOGL": {"pe_ratio": 24.7,  "market_cap": 2_100_000_000_000},
    "AMZN":  {"pe_ratio": 40.1,  "market_cap": 1_900_000_000_000},
    "NVDA":  {"pe_ratio": 55.3,  "market_cap": 2_700_000_000_000},
    "META":  {"pe_ratio": 23.6,  "market_cap": 1_200_000_000_000},
    "TSLA":  {"pe_ratio": 60.8,  "market_cap": 800_000_000_000},
    "LLY":   {"pe_ratio": 115.2, "market_cap": 790_000_000_000},
    "AVGO":  {"pe_ratio": 68.4,  "market_cap": 650_000_000_000},
    "BRK.B": {"pe_ratio": 20.3,  "market_cap": 890_000_000_000},
    "JPM":   {"pe_ratio": 12.4,  "market_cap": 580_000_000_000},
    "BAC":   {"pe_ratio": 11.9,  "market_cap": 310_000_000_000},
    "GS":    {"pe_ratio": 13.2,  "market_cap": 145_000_000_000},
    "V":     {"pe_ratio": 31.5,  "market_cap": 530_000_000_000},
    "MA":    {"pe_ratio": 33.7,  "market_cap": 420_000_000_000},
    "JNJ":   {"pe_ratio": 15.8,  "market_cap": 370_000_000_000},
    "UNH":   {"pe_ratio": 19.3,  "market_cap": 460_000_000_000},
    "PFE":   {"pe_ratio": 13.1,  "market_cap": 160_000_000_000},
    "ABBV":  {"pe_ratio": 16.4,  "market_cap": 280_000_000_000},
    "XOM":   {"pe_ratio": 14.2,  "market_cap": 520_000_000_000},
    "CVX":   {"pe_ratio": 13.8,  "market_cap": 280_000_000_000},
    "DIA":   {"pe_ratio": 20.1,  "market_cap": 30_000_000_000},
    "IWM":   {"pe_ratio": 18.5,  "market_cap": 60_000_000_000},
    "VTI":   {"pe_ratio": 21.3,  "market_cap": 420_000_000_000},
}

# Realistic mock candle data per ticker
_CANDLES = {
    "AAPL":  {"close": 189.50, "volume": 55_000_000},
    "MSFT":  {"close": 415.20, "volume": 22_000_000},
    "SPY":   {"close": 524.80, "volume": 80_000_000},
    "QQQ":   {"close": 448.30, "volume": 45_000_000},
    "GOOGL": {"close": 175.40, "volume": 25_000_000},
    "AMZN":  {"close": 192.70, "volume": 35_000_000},
    "NVDA":  {"close": 131.20, "volume": 200_000_000},
    "META":  {"close": 574.60, "volume": 18_000_000},
    "TSLA":  {"close": 248.90, "volume": 90_000_000},
    "LLY":   {"close": 812.40, "volume": 3_500_000},
    "AVGO":  {"close": 185.30, "volume": 14_000_000},
    "BRK.B": {"close": 441.20, "volume": 4_800_000},
    "JPM":   {"close": 218.40, "volume": 12_000_000},
    "BAC":   {"close": 43.20,  "volume": 40_000_000},
    "GS":    {"close": 495.10, "volume": 3_000_000},
    "V":     {"close": 277.30, "volume": 8_000_000},
    "MA":    {"close": 472.80, "volume": 4_000_000},
    "JNJ":   {"close": 152.60, "volume": 7_000_000},
    "UNH":   {"close": 311.50, "volume": 5_000_000},
    "PFE":   {"close": 26.80,  "volume": 30_000_000},
    "ABBV":  {"close": 188.40, "volume": 6_000_000},
    "XOM":   {"close": 114.20, "volume": 18_000_000},
    "CVX":   {"close": 158.70, "volume": 10_000_000},
    "DIA":   {"close": 391.20, "volume": 5_000_000},
    "IWM":   {"close": 208.40, "volume": 28_000_000},
    "VTI":   {"close": 260.10, "volume": 4_000_000},
}


def fetch_financials(ticker: str) -> dict:
    t = ticker.upper()
    if t not in ALLOWED_TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker '{t}' not in approved asset universe")
    data = _FINANCIALS.get(t, {"pe_ratio": 20.0, "market_cap": 100_000_000_000})
    return {"ticker": t, **data}


def fetch_candles(ticker: str, period: str) -> dict:
    t = ticker.upper()
    if t not in ALLOWED_TICKERS:
        raise HTTPException(status_code=404, detail=f"Ticker '{t}' not in approved asset universe")
    data = _CANDLES.get(t, {"close": 100.00, "volume": 1_000_000})
    return {"ticker": t, "period": period, **data}
