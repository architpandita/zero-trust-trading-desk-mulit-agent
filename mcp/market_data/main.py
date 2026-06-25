from fastapi import FastAPI
from mcp.market_data.data_service import fetch_financials, fetch_candles
from mcp.market_data.hash_utils import generate_data_hash

app = FastAPI()

@app.get("/market_data/fetch_financials")
def api_fetch_financials(ticker: str):
    data = fetch_financials(ticker)
    data["data_hash"] = generate_data_hash(data)
    return data

@app.get("/market_data/fetch_candles")
def api_fetch_candles(ticker: str, period: str):
    data = fetch_candles(ticker, period)
    data["data_hash"] = generate_data_hash(data)
    return data
