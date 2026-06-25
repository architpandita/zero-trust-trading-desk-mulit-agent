import yaml
from agents.execution.schemas import TradeProposal, PolicyResult

class DataIntegrityError(Exception):
    pass

class PolicyViolationError(Exception):
    pass

class PolicyServer:
    def __init__(self, config_path: str = "config/policy_config.yaml"):
        with open(config_path) as f:
            self.policy = yaml.safe_load(f)

    def validate(self, proposal: TradeProposal) -> PolicyResult:
        if not proposal.provenance:
            raise PolicyViolationError("Missing provenance")
            
        expected_hash = proposal.provenance[0].response_sha256
        if proposal.data_hash != expected_hash:
            raise DataIntegrityError("Hash mismatch")

        allowed_tickers = self.policy["asset_universe"]["allowed_tickers"]
        if proposal.ticker not in allowed_tickers:
            raise PolicyViolationError(f"Ticker {proposal.ticker} not allowed")

        max_size = self.policy["global_risk_mandate"]["max_single_trade_value_usd"]
        if proposal.estimated_value_usd > max_size:
            raise PolicyViolationError("Trade size exceeds limit")

        hitl_threshold = self.policy["human_in_the_loop_triggers"]["require_hitl_if_trade_value_exceeds"]
        if proposal.estimated_value_usd > hitl_threshold:
            return PolicyResult(
                session_id=proposal.session_id,
                passed=True,
                decision_code="PENDING_HITL",
                hitl_required=True
            )

        return PolicyResult(
            session_id=proposal.session_id,
            passed=True,
            decision_code="EXECUTED"
        )
