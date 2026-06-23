import yaml
from typing import List, Dict, Tuple, Optional
from pydantic import BaseModel, Field

# ==============================================================================
# PYDANTIC SCHEMAS FOR CONFIGURATION
# ==============================================================================

class GlobalRiskMandate(BaseModel):
    max_portfolio_exposure_usd: float
    max_single_trade_value_usd: float
    max_daily_drawdown_percent: float
    halt_trading_on_drawdown: bool

class AssetUniverse(BaseModel):
    allowed_tickers: List[str]
    restricted_asset_classes: List[str]

class AgentPermission(BaseModel):
    role: str
    execution_auth: bool
    allowed_tools: List[str]

class HumanInTheLoopTriggers(BaseModel):
    require_hitl_if_trade_value_exceeds: float
    require_hitl_if_sentiment_conflict: bool
    require_hitl_on_first_trade_of_day: bool

class ContextHygieneConfig(BaseModel):
    mask_account_balance: bool
    mask_api_keys: bool

class PolicyConfig(BaseModel):
    version: str
    environment: str
    global_risk_mandate: GlobalRiskMandate
    asset_universe: AssetUniverse
    agent_permissions: Dict[str, AgentPermission]
    human_in_the_loop_triggers: HumanInTheLoopTriggers
    context_hygiene: ContextHygieneConfig

# ==============================================================================
# PYDANTIC SCHEMA FOR TRADE PROPOSAL
# ==============================================================================

class TradeProposal(BaseModel):
    ticker: str
    action: str  # "BUY" or "SELL"
    quantity: int
    price: float
    agent_role: str  # e.g., "execution_agent", "fundamental_agent"
    asset_class: str = "EQUITY"  # "EQUITY", "CRYPTO", "PENNY_STOCKS", etc.
    sentiment_conflict: bool = False
    first_trade_of_day: bool = False

# ==============================================================================
# POLICY SERVER GATEWAY
# ==============================================================================

class PolicyServer:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config: PolicyConfig = self._load_config()

    def _load_config(self) -> PolicyConfig:
        with open(self.config_path, "r") as f:
            raw_data = yaml.safe_load(f)
        return PolicyConfig(**raw_data)

    def validate_proposal(
        self, proposal: TradeProposal, current_portfolio_exposure: float = 0.0
    ) -> Tuple[str, List[str]]:
        """
        Validates a trade proposal against the loaded policy config.
        Returns:
            Tuple[str, List[str]]: (decision, messages)
            decision can be: "DENY", "HITL", or "ALLOW"
        """
        denial_reasons = []
        hitl_reasons = []

        trade_value = proposal.quantity * proposal.price

        # 1. Check Agent Permission
        agent_perm = self.config.agent_permissions.get(proposal.agent_role)
        if not agent_perm:
            denial_reasons.append(f"Agent role '{proposal.agent_role}' has no permissions defined in policy.")
        elif not agent_perm.execution_auth:
            denial_reasons.append(f"Agent role '{proposal.agent_role}' does not possess execution authority.")

        # 2. Check Asset Universe
        ticker_upper = proposal.ticker.upper()
        if ticker_upper not in [t.upper() for t in self.config.asset_universe.allowed_tickers]:
            denial_reasons.append(f"Ticker '{proposal.ticker}' is not in the allowed tickers list.")

        # 3. Check Restricted Asset Classes
        asset_class_upper = proposal.asset_class.upper()
        if asset_class_upper in [ac.upper() for ac in self.config.asset_universe.restricted_asset_classes]:
            denial_reasons.append(f"Asset class '{proposal.asset_class}' is explicitly restricted by policy.")

        # 4. Check Single Trade Value Limit
        max_trade_val = self.config.global_risk_mandate.max_single_trade_value_usd
        if trade_value > max_trade_val:
            denial_reasons.append(
                f"Trade value ${trade_value:,.2f} exceeds max single trade value limit of ${max_trade_val:,.2f}."
            )

        # 5. Check Portfolio Exposure Limit
        max_portfolio_exposure = self.config.global_risk_mandate.max_portfolio_exposure_usd
        projected_exposure = current_portfolio_exposure + trade_value
        if projected_exposure > max_portfolio_exposure:
            denial_reasons.append(
                f"Projected portfolio exposure ${projected_exposure:,.2f} (current: ${current_portfolio_exposure:,.2f} + trade: ${trade_value:,.2f}) "
                f"exceeds global limit of ${max_portfolio_exposure:,.2f}."
            )

        # If there are any denial reasons, reject immediately (Zero-Trust Hard Gate)
        if denial_reasons:
            return "DENY", denial_reasons

        # 6. Check Human-in-the-Loop Triggers
        hitl_triggers = self.config.human_in_the_loop_triggers
        
        if trade_value > hitl_triggers.require_hitl_if_trade_value_exceeds:
            hitl_reasons.append(
                f"Trade value ${trade_value:,.2f} exceeds HITL threshold of ${hitl_triggers.require_hitl_if_trade_value_exceeds:,.2f}."
            )
        
        if proposal.sentiment_conflict and hitl_triggers.require_hitl_if_sentiment_conflict:
            hitl_reasons.append("Sentiment conflict detected (disagreement between fundamental and technical analysis).")

        if proposal.first_trade_of_day and hitl_triggers.require_hitl_on_first_trade_of_day:
            hitl_reasons.append("This is the first trade of the day.")

        if hitl_reasons:
            return "HITL", hitl_reasons

        return "ALLOW", ["Trade proposal validated successfully and matches all risk guardrails."]
