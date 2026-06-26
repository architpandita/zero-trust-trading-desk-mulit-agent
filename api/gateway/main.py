import asyncio
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os

BROKER_MCP_URL = os.getenv("BROKER_MCP_URL", "http://localhost:8002")

from agents.orchestrator import orchestrator as orch
from agents.eval.scenario_agents import (
    ScenarioFundamentalAgent,
    ScenarioTechnicalAgent,
    ScenarioExecutionAgent,
)

app = FastAPI(title="Zero-Trust API Gateway (BFF)", version="1.0.0")

# Allow requests from the React frontend (usually port 5173 for Vite dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_MANAGER_URL = os.getenv("STATE_MANAGER_URL", "http://localhost:8003")

@app.on_event("startup")
async def startup_event():
    # Initialize the scenario agents (acting as our mock LLM swarm)
    orch.fundamental_agent = ScenarioFundamentalAgent()
    orch.technical_agent = ScenarioTechnicalAgent()
    orch.execution_agent = ScenarioExecutionAgent()

class ExecuteRequest(BaseModel):
    directive: str

@app.post("/api/execute")
async def execute_directive(req: ExecuteRequest):
    """Passes the instruction prompt to the multi-agent orchestrator."""
    result = await orch.run_swarm_session(req.directive)
    return result.model_dump()

@app.get("/api/health")
async def get_health():
    """Proxies the health check to the State Manager."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{STATE_MANAGER_URL}/api/v1/health", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"State Manager unreachable: {str(e)}")

@app.get("/api/pending")
async def get_pending():
    """Proxies the pending HITL queue request to the State Manager."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{STATE_MANAGER_URL}/api/v1/pending", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"State Manager unreachable: {str(e)}")

class DecisionRequest(BaseModel):
    action: str

@app.post("/api/decision/{session_id}")
async def post_decision(session_id: str, decision: DecisionRequest):
    """Forwards the HITL decision (APPROVE/DENY) to the State Manager."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{STATE_MANAGER_URL}/api/v1/decision/{session_id}",
                json=decision.model_dump(),
                timeout=5.0
            )
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Pending trade not found")
            resp.raise_for_status()
            return resp.json()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"State Manager unreachable: {str(e)}")


@app.get("/api/audit")
async def get_audit():
    """Proxies the audit log from the State Manager (last 100 entries)."""
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{STATE_MANAGER_URL}/api/v1/audit", timeout=5.0)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"State Manager unreachable: {str(e)}")


@app.get("/api/portfolio")
async def get_portfolio():
    """Proxies portfolio holdings and trades from the mock broker."""
    async with httpx.AsyncClient() as client:
        try:
            holdings_resp = await client.get(f"{BROKER_MCP_URL}/kite/portfolio/holdings", timeout=5.0)
            trades_resp = await client.get(f"{BROKER_MCP_URL}/kite/trades", timeout=5.0)
            holdings = holdings_resp.json().get("data", []) if holdings_resp.status_code == 200 else []
            trades = trades_resp.json().get("data", []) if trades_resp.status_code == 200 else []
            return {"holdings": holdings, "trades": trades}
        except Exception as e:
            # Return empty portfolio gracefully so UI doesn't crash
            return {"holdings": [], "trades": [], "error": str(e)}
