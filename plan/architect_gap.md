ARCHITECTURE_E2E.md: End-to-End System Architecture Specification
1. Executive Summary & Core Use Cases
This document details the production-grade end-to-end (E2E) architecture for the Zero-Trust Multi-Agent Trading Desk. The framework resolves the structural vulnerability of Ambient Authority in autonomous financial systems by treating AI agents as untrusted processing entities. All data gathering, state synchronization, and execution commands pass through explicit, deterministic verification frameworks.

Use Case Scenario A: Compliant Trading Flow (The Success Path)
Ingest & Sanitize: The human operator inputs a natural language directive. The deterministic Security Middleware (Python Regex) scrubs the input for explicit adversarial tokens.

Parallel Swarm (Fork): The Orchestrator uses asyncio.gather() to trigger the Fundamental Agent and Technical Agent simultaneously and independently. They fetch mocked market data via local FastAPI Model Context Protocol (MCP) endpoints.

Deterministic Consensus (Join): A deterministic Python script evaluates both independent agent outputs. If signals conflict (e.g., BUY vs. SELL), the system defaults to "Fail Closed" (Reject/Hold). If they agree, data flows to the Execution Agent.

Data Provenance & Typing: The Execution Agent compiles the consensus into a strictly typed Pydantic JSON proposal, appending a cryptographic SHA256 data_hash of the market feed to mathematically prove it did not hallucinate the data.

Zero-Trust Gate: The Policy Server intercepts the Pydantic payload, validates the schema, verifies the data hash, and checks execution limits against policy_config.yaml.

Asynchronous HITL: If the trade exceeds $1,000, the Policy Server routes the state to a lightweight local SQLite datastore.

Execution, Telemetry & Amnesia: The operator reviews the "Vibe Diff" via the Streamlit A2UI Portal, clicks approve, and posts the execution to the Mock Broker API. The trade metadata is sent to the Telemetry Logger for future prompt-tuning, and the active session RAM is aggressively purged.

2. Comprehensive System Architecture Diagram
The architecture utilizes a low-latency parallel execution graph, isolated FastAPI mock services, and a dedicated telemetry feedback loop for continuous improvement.

Code snippet
graph TD
    %% Frontend and State Management
    UI[A2UI Portal: Streamlit] --> |Polls Pending State| DB[(Local State: SQLite)]
    UI --> |POST Approve/Reject| API_GATE[FastAPI State Router]

    %% Input & Security Boundary
    User[User Prompt] --> SM[Security Middleware: Deterministic Python Filter]
    SM --> SO[Swarm Orchestrator: asyncio]

    %% Parallel Agent Execution (Fork/Join)
    subgraph Swarm Core (Ephemeral State)
        SO --> |Fork| FA[Fundamental Agent]
        SO --> |Fork| TA[Technical Agent]
        FA & TA --> |Join: Fail-Closed| CON[Deterministic Consensus Gate]
        CON --> EA[Execution Agent: Generates Pydantic & Hash]
    end

    %% Model Context Protocol Layer
    subgraph Protocol Gateway (FastAPI MCP Mock Services)
        FA & TA --> |HTTP GET| MCP_DATA[FastAPI Data Service: yfinance/mock]
        EA --> |Tool Call| MCP_SECURE[FastAPI Broker Service: secure/mock]
    end

    %% Policy Boundaries and Gates
    EA --> PS{Deterministic Policy Server}
    PS --> |Hash Mismatch / Schema Fail| REJ[Hard Boundary: Context Flush & Reject]
    PS --> |Valid & > $1000| HITL[Route to Pending State DB]
    PS --> |Valid & < $1000| MB[FastAPI Mock Broker Execution]
    
    API_GATE --> |User Approves| MB
    API_GATE --> |User Denies| REJ

    %% Observability & Continuous Improvement
    MB --> |Async Log| TELEM[(Audit & Telemetry DB)]
    REJ --> |Async Log| TELEM
    
    %% Development & CI/CD Pipeline Tracking
    subgraph LLMOps QA Environment
        EV[Security Eval Agent: LLM-as-a-Judge] --> |Pre-Merge Red-Team Test| Swarm Core
    end
3. Agentic Communications & Protocol Standards
Parallel Execution & Deterministic Consensus (Fork/Join)
To eliminate latency and prevent infinite agent debate loops, agents run concurrently and completely independently.

Fork: asyncio.gather(fundamental_task(), technical_task())

Join: A strict Python function merges the two structured outputs. If signals diverge, the system executes a "Fail Closed" risk management protocol, terminating the trade proposal.

Model Context Protocol (MCP) via FastAPI
Tools are decoupled from the LLMs using local FastAPI endpoints to maintain rapid local development without Docker networking overhead.

localhost:8001 (Mock Data): Returns deterministic market payloads and includes a SHA256 hash of the response body.

localhost:8002 (Mock Broker): Receives validated orders. LLMs have zero direct access to this routing layer.

4. System Data Contracts & Configuration
Root Policy Specification (policy_config.yaml)
The deterministic source of truth for runtime validation.

YAML
version: "1.2.0"
environment: "local_mock"

global_risk_mandate:
  max_portfolio_exposure_usd: 10000.00
  max_single_trade_value_usd: 2500.00

agent_permissions:
  fundamental_agent:
    execution_auth: false
  technical_agent:
    execution_auth: false
  execution_agent:
    execution_auth: true
    allowed_mcp_tools: ["secure_broker/submit_order_proposal"]

human_in_the_loop_triggers:
  require_hitl_if_trade_value_exceeds: 1000.00
  fail_closed_on_consensus_mismatch: true
The Data Provenance Contract (Pydantic Schema)
The Execution Agent must yield this strict JSON object. The inclusion of the data_hash provides mathematical proof that the agent did not hallucinate the pricing data.

Python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class TradeProposal(BaseModel):
    session_id: str
    ticker: str
    action: Literal["BUY", "SELL", "HOLD"]
    quantity: int = Field(gt=0)
    estimated_value_usd: float = Field(gt=0.0)
    vibe_diff: str = Field(min_length=20, description="Plain English structural logic summary for UI")
    data_hash: str = Field(min_length=64, description="SHA256 hash of the MCP data payload utilized")

    @field_validator('ticker')
    @classmethod
    def validate_ticker(cls, value: str) -> str:
        if not value.isupper() or len(value) > 5:
            raise ValueError("Invalid ticker format.")
        return value
5. Security, LLMOps & Evaluation
Shift-Left LLM Security (The Eval Agent)
Rather than executing an expensive LLM to scan every live trade, the system utilizes a Security Eval Agent during the CI/CD testing phase. This LLM acts as an automated Red-Team, generating prompt injections and feeding them to the Swarm Core to ensure the Deterministic Policy Server catches them before the code is merged into production.

Runtime Deterministic Firewall
Ingest Filter: Python string matching blocks adversarial payload parameters ("system bypass").

Provenance & Schema Gate: The Policy Server validates the Pydantic structure and recalculates the SHA256 hash of the market data. A hash mismatch results in a hard-rejection.

6. Observability & Continuous Improvement
Audit & Telemetry Logging
To ensure the agents' performance can be monitored and improved without violating the "Ephemeral State" security rule, the system implements asynchronous logging.

Upon trade execution or rejection, the live session_data RAM object is purged.

However, metadata (the initial prompt, the Pydantic TradeProposal, the vibe_diff, and the Policy Server's execution/rejection code) is asynchronously written to an Audit & Telemetry DB.

Feedback Loop: This telemetry allows the engineering team to review agent reasoning drift over time, evaluate rejection rates, and fine-tune the system prompts in future iterations.

7. Execution & UI Orchestration
The A2UI flow is strictly decoupled from the agent processing loop.

State Manager (FastAPI): Holds pending trades inside a local SQLite database.

The Dashboard (Streamlit): Periodically polls the FastAPI state manager. When a pending_hitl state is detected, the UI renders the vibe_diff. Clicking "Approve" triggers a deterministic POST request to the FastAPI broker endpoint to complete the trade.