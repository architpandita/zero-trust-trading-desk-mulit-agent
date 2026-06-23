from typing import Dict, Tuple, List
import json
import os
from datetime import datetime

class MockBroker:
    def __init__(self, initial_cash: float = 10000.00, log_file: str = "broker_ledger.json"):
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}
        self.log_file = log_file
        self.ledger: List[Dict] = []
        
        # Clear log file if it exists to start fresh for the demo
        if os.path.exists(self.log_file):
            try:
                os.remove(self.log_file)
            except Exception:
                pass

    def get_portfolio_exposure(self, current_prices: Dict[str, float]) -> float:
        """
        Calculates the total exposure (value of all held stock positions).
        """
        exposure = 0.0
        for ticker, qty in self.positions.items():
            price = current_prices.get(ticker.upper(), 0.0)
            exposure += qty * price
        return exposure

    def get_total_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Total value = Cash + Stock value (exposure).
        """
        return self.cash + self.get_portfolio_exposure(current_prices)

    def execute_trade(
        self, ticker: str, action: str, quantity: int, price: float
    ) -> Tuple[bool, str]:
        """
        Executes a trade against the mock cash and positions.
        Returns:
            Tuple[bool, str]: (Success, message)
        """
        ticker_upper = ticker.upper()
        action_upper = action.upper()
        trade_value = quantity * price

        if action_upper == "BUY":
            if self.cash < trade_value:
                return False, f"Insufficient funds: trade value is ${trade_value:,.2f} but available cash is ${self.cash:,.2f}."
            
            self.cash -= trade_value
            self.positions[ticker_upper] = self.positions.get(ticker_upper, 0) + quantity
            msg = f"SUCCESS: Bought {quantity} shares of {ticker_upper} at ${price:,.2f}/share for total of ${trade_value:,.2f}."
            self._log_transaction(ticker_upper, action_upper, quantity, price, msg)
            return True, msg

        elif action_upper == "SELL":
            current_qty = self.positions.get(ticker_upper, 0)
            if current_qty < quantity:
                return False, f"Insufficient shares: attempted to sell {quantity} of {ticker_upper} but only hold {current_qty} shares."

            self.cash += trade_value
            self.positions[ticker_upper] = current_qty - quantity
            if self.positions[ticker_upper] == 0:
                del self.positions[ticker_upper]
                
            msg = f"SUCCESS: Sold {quantity} shares of {ticker_upper} at ${price:,.2f}/share for total of ${trade_value:,.2f}."
            self._log_transaction(ticker_upper, action_upper, quantity, price, msg)
            return True, msg

        else:
            return False, f"Unsupported broker action: {action}."

    def _log_transaction(self, ticker: str, action: str, quantity: int, price: float, log_message: str):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": price,
            "total_value": quantity * price,
            "remaining_cash": self.cash,
            "positions": self.positions.copy(),
            "message": log_message
        }
        self.ledger.append(entry)
        
        # Write to JSON ledger log
        with open(self.log_file, "w") as f:
            json.dump(self.ledger, f, indent=2)
