import re
from typing import Dict, List, Tuple

# ==============================================================================
# CONTEXT HYGIENE MIDDLEWARE
# ==============================================================================

class ContextHygiene:
    """
    Prevents leak of sensitive data (PII, API Keys, Account Balances)
    to external LLMs/Prompt streams.
    """
    @staticmethod
    def sanitize_context(raw_text: str) -> str:
        # Mask API Keys (e.g., sk-..., API_KEY=...)
        sanitized = re.sub(
            r'(?i)(api[_-]?key\s*[:=]\s*[\'"]?)([a-zA-Z0-9_\-]{8,})([\'"]?)',
            r'\1[MASKED_API_KEY_ENTROPY]\3',
            raw_text
        )
        # Mask secrets in env-like variables
        sanitized = re.sub(
            r'(?i)(secret\s*[:=]\s*[\'"]?)([a-zA-Z0-9_\-]{8,})([\'"]?)',
            r'\1[MASKED_SECRET]\3',
            sanitized
        )
        # Mask Account balances/Cash amounts
        sanitized = re.sub(
            r'(?i)(account[_-]?balance|broker[_-]?cash)\s*[:=]\s*([0-9]+\.[0-9]+)',
            r'\1: [MASKED_BALANCE_FOR_LLM_HYGIENE]',
            sanitized
        )
        return sanitized


# ==============================================================================
# CORE AGENTS OF THE DELIBERATION SWARM
# ==============================================================================

class TechnicalAgent:
    """
    Analyzes technical stock indicators (Moving Averages, RSI).
    """
    def __init__(self):
        self.system_prompt = (
            "ROLE: Technical Analysis Agent\n"
            "OBJECTIVE: Analyze short-term price momentum and volume trends.\n"
            "CONSTRAINTS: Cannot write trade proposals or access broker API keys. "
            "Only output analytical opinions and recommendations."
        )

    def analyze(self, ticker: str, price_history: List[float]) -> Dict[str, any]:
        if not price_history or len(price_history) < 5:
            return {"recommendation": "HOLD", "reason": "Insufficient price data for technical indicators."}

        current_price = price_history[-1]
        # Calculate a simple 5-day Moving Average (SMA-5)
        sma_5 = sum(price_history[-5:]) / 5
        
        # Simple Technical Indicator Decision Rules
        if current_price > sma_5:
            recommendation = "BUY"
            reason = f"Current price (${current_price:.2f}) is above the 5-day SMA (${sma_5:.2f}). Bullish momentum."
        elif current_price < sma_5:
            recommendation = "SELL"
            reason = f"Current price (${current_price:.2f}) is below the 5-day SMA (${sma_5:.2f}). Bearish momentum."
        else:
            recommendation = "HOLD"
            reason = f"Current price (${current_price:.2f}) is aligned with the 5-day SMA (${sma_5:.2f}). Consolidation."

        return {
            "agent": "TechnicalAgent",
            "ticker": ticker.upper(),
            "recommendation": recommendation,
            "metric_checked": f"SMA-5: {sma_5:.2f}",
            "reasoning": reason
        }


class FundamentalAgent:
    """
    Evaluates corporate health and macroeconomic sentiment.
    """
    def __init__(self):
        self.system_prompt = (
            "ROLE: Fundamental Analysis Agent\n"
            "OBJECTIVE: Evaluate intrinsic value through metrics (P/E ratio, Revenue Growth) and news sentiment.\n"
            "CONSTRAINTS: Isolated from broker credentials. Only outputs valuation summaries."
        )

    def analyze(self, ticker: str, fundamentals: Dict[str, any]) -> Dict[str, any]:
        pe_ratio = fundamentals.get("pe_ratio", 20.0)
        revenue_growth = fundamentals.get("revenue_growth", 0.05) # e.g. 5%
        news_sentiment = fundamentals.get("news_sentiment", "neutral").lower()

        # Decision rules
        score = 0
        if pe_ratio < 25: score += 1  # Favorable P/E
        if revenue_growth > 0.10: score += 1  # Double-digit growth
        if news_sentiment == "bullish": score += 1
        elif news_sentiment == "bearish": score -= 1

        if score >= 2:
            recommendation = "BUY"
            reason = f"Solid fundamentals (P/E: {pe_ratio}, Growth: {revenue_growth:.1%}) and {news_sentiment} news sentiment."
        elif score <= -1:
            recommendation = "SELL"
            reason = f"Weak fundamentals or bearish news sentiment (P/E: {pe_ratio}, sentiment: {news_sentiment})."
        else:
            recommendation = "HOLD"
            reason = f"Moderate metrics (P/E: {pe_ratio}, Growth: {revenue_growth:.1%}) and {news_sentiment} news sentiment."

        return {
            "agent": "FundamentalAgent",
            "ticker": ticker.upper(),
            "recommendation": recommendation,
            "reasoning": reason,
            "sentiment": news_sentiment
        }


class ExecutionAgent:
    """
    Coordinates recommendations, checks for conflicts, and structures proposals.
    """
    def __init__(self):
        self.system_prompt = (
            "ROLE: Execution Orchestrator Agent\n"
            "OBJECTIVE: Gather analyses from Fundamental & Technical agents. Synthesize signals.\n"
            "OUTPUT FORMAT: Validated JSON trade proposals. No execution rights."
        )

    def generate_proposal(
        self, 
        ticker: str, 
        tech_rec: Dict[str, any], 
        fund_rec: Dict[str, any],
        quantity: int,
        price: float,
        first_trade_of_day: bool = False
    ) -> Tuple[Dict[str, any], str]:
        """
        Synthesizes technical and fundamental opinions into a structured trade proposal.
        Also outputs a 'Vibe Diff' summary justifying the trade.
        """
        ticker_upper = ticker.upper()
        
        # Determine consolidated action
        tr_rec = tech_rec.get("recommendation", "HOLD")
        fr_rec = fund_rec.get("recommendation", "HOLD")

        # Conflict check
        sentiment_conflict = (tr_rec != fr_rec) and (tr_rec != "HOLD" and fr_rec != "HOLD")

        # Basic consensus matching
        if tr_rec == "BUY" and fr_rec == "BUY":
            action = "BUY"
        elif tr_rec == "SELL" or fr_rec == "SELL":
            action = "SELL"  # Play it safe, execute sells if any signal is bearish
        else:
            action = "HOLD"

        # Generate proposal JSON
        proposal = {
            "ticker": ticker_upper,
            "action": action,
            "quantity": quantity,
            "price": price,
            "agent_role": "execution_agent",
            "sentiment_conflict": sentiment_conflict,
            "first_trade_of_day": first_trade_of_day
        }

        # Generate "Vibe Diff" (Plain-English summary of agent reasoning)
        vibe_diff = (
            f"=== AGENT DELIBERATION SUMMARY (VIBE DIFF) ===\n"
            f"Asset: {ticker_upper} | Proposed Action: {action} {quantity} shares @ ${price:.2f}/share\n"
            f"--------------------------------------------------\n"
            f"Technical Agent: {tech_rec['recommendation']} - {tech_rec['reasoning']}\n"
            f"Fundamental Agent: {fund_rec['recommendation']} - {fund_rec['reasoning']}\n"
            f"Consensus Status: {'CONFLICT (Triggers HITL)' if sentiment_conflict else 'Consensus Aligned'}\n"
            f"=================================================="
        )

        return proposal, vibe_diff
