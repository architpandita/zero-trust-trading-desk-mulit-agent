from fastapi import APIRouter
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter(prefix="/kite")

# In-memory storage for the mock broker
_orders = {}
_trades = []
_portfolio = {
    "cash": 100000.0,
    "holdings": [{"tradingsymbol": "AAPL", "quantity": 50, "average_price": 140.0}]
}

class OrderRequest(BaseModel):
    tradingsymbol: str
    transaction_type: str # BUY or SELL
    quantity: int
    order_type: str = "MARKET"
    price: float = 0.0

@router.post("/orders/regular")
def place_order(order: OrderRequest):
    """Mock placing a BUY or SELL order"""
    order_id = str(uuid.uuid4())[:8]
    order_data = {
        "order_id": order_id,
        "status": "COMPLETE", # Auto-complete for mock simplicity
        "tradingsymbol": order.tradingsymbol,
        "transaction_type": order.transaction_type,
        "quantity": order.quantity,
        "order_timestamp": datetime.utcnow().isoformat()
    }
    _orders[order_id] = order_data
    
    # Auto-generate a trade for the completed order
    trade_id = str(uuid.uuid4())[:8]
    fill_price = order.price if order.price > 0 else 150.0
    _trades.append({
        "trade_id": trade_id,
        "order_id": order_id,
        "tradingsymbol": order.tradingsymbol,
        "transaction_type": order.transaction_type,
        "quantity": order.quantity,
        "fill_price": fill_price
    })
    
    # Update portfolio holdings and cash
    qty = order.quantity
    symbol = order.tradingsymbol
    tx_type = order.transaction_type.upper()
    
    holdings = _portfolio["holdings"]
    existing = next((h for h in holdings if h["tradingsymbol"] == symbol), None)
    
    if tx_type == "BUY":
        if existing:
            total_cost = (existing["quantity"] * existing["average_price"]) + (qty * fill_price)
            existing["quantity"] += qty
            existing["average_price"] = round(total_cost / existing["quantity"], 2)
        else:
            holdings.append({
                "tradingsymbol": symbol,
                "quantity": qty,
                "average_price": fill_price
            })
        _portfolio["cash"] -= (qty * fill_price)
    elif tx_type == "SELL":
        if existing:
            if existing["quantity"] >= qty:
                existing["quantity"] -= qty
                _portfolio["cash"] += (qty * fill_price)
                if existing["quantity"] == 0:
                    holdings.remove(existing)
            else:
                real_qty = existing["quantity"]
                existing["quantity"] = 0
                holdings.remove(existing)
                _portfolio["cash"] += (real_qty * fill_price)
                
    return {"status": "success", "data": {"order_id": order_id}}

@router.get("/orders/{order_id}")
def get_order_details(order_id: str):
    """Mock fetching order details"""
    if order_id in _orders:
        return {"status": "success", "data": [_orders[order_id]]}
    return {"status": "error", "message": "Order not found"}

@router.get("/trades")
def get_trades():
    """Mock fetching all trades"""
    return {"status": "success", "data": _trades}

@router.get("/portfolio/holdings")
def get_portfolio():
    """Mock fetching portfolio holdings"""
    return {"status": "success", "data": _portfolio["holdings"]}
