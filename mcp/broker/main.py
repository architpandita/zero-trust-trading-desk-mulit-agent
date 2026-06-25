from fastapi import FastAPI
from mcp.broker.policy_server import PolicyServer, PolicyViolationError, DataIntegrityError
from agents.execution.schemas import TradeProposal
from mcp.broker.mock_kite import router as kite_router

app = FastAPI()
app.include_router(kite_router)

policy_server = PolicyServer("config/policy_config.yaml")

@app.post("/secure_broker/submit_order_proposal")
def submit_order_proposal(proposal: TradeProposal):
    try:
        result = policy_server.validate(proposal)
        return {"decision_code": result.decision_code}
    except PolicyViolationError as e:
        return {"decision_code": "REJECTED_POLICY", "reason": str(e)}
    except DataIntegrityError as e:
        return {"decision_code": "REJECTED_HASH_MISMATCH", "reason": str(e)}

@app.get("/secure_broker/get_portfolio_balance")
def get_portfolio_balance():
    return {"balance": "[MASKED_BALANCE]", "status": "active"}
