# ARCHITECTURE_E2E.md: End-to-End System Architecture Specification
# todo update the architure for mointering and feedback for agent performece n improvement

## 1. Executive Summary & Core Use Cases
This document details the production-grade end-to-end (E2E) architecture for the **Zero-Trust Multi-Agent Trading Desk**. The framework resolves the structural vulnerability of **Ambient Authority** in autonomous financial systems by handling AI agents as untrusted software entities. All data gathering, state synchronization, and execution commands pass through explicit, deterministic verification frameworks.

### Use Case Scenario A: Compliant Trading Flow (The Success Path)
1. The human operator inputs a natural language directive for analysis and potential allocation via the **Agent-to-UI (A2UI)** interface.
2. The **Swarm Orchestrator** instantiates a shared blackboard state context.
3. The **Fundamental** and **Technical** agents communicate horizontally via Agent-to-Agent (A2A) pathways to evaluate conditions, utilizing read-only **Model Context Protocol (MCP)** endpoints.
4. The **Security Agent** audits the live discussion log for context hygiene, stripping potential leaks or anomalous token spikes.
5. The **Execution Agent** compiles the data into a strictly typed Pydantic JSON proposal.
6. The **Policy Server** intercepts the payload, flags that the valuation exceeds standard auto-execute thresholds, and holds execution pending human sign-off.
7. The operator approves the trade via the **A2UI Portal**, committing the order safely to the **Mock Broker API**.

### Use Case Scenario B: Compromised Prompt Injection Defense (The Threat Path)
1. Malicious input strings (e.g., adversarial prompt overrides via market data feeds or forced inputs) attempt to hijack agent workflows.
2. The **Security Agent** intercepts and sanitizes basic structural tokens at the ingest boundary.
3. If an adversarial strategy bypasses initial filtering and influences an agent to formulate out-of-universe trades, the **Execution Agent** attempts to post an invalid structural format.
4. The **Policy Server** serves as the definitive firewall, testing the incoming JSON directly against the root `policy_config.yaml`.
5. The validation fails programmatically. The execution pipeline is terminated instantly, throwing a strict system error back to the logs, and completely purging the active LLM context without interacting with any financial endpoint.

---

## 2. Comprehensive System Architecture Diagram
The layout below illustrates the strict programmatic isolation between the collaborative agent execution context, the secure transport protocol framework, and the final deterministic safety gatekeepers.

```mermaid
graph TD
    %% Frontend and UI Orchestration
    UI[A2UI Frontend Portal: Streamlit] <--> |SSE / JSON-RPC| SO[Swarm Orchestrator]

    %% Distributed Swarm Core (A2A Blackboard Channel)
    subgraph Swarm Core (Horizontal A2A Communication)
        SO <--> FA[Fundamental Agent]
        SO <--> TA[Technical Agent]
        FA <--> TA
        FA & TA <--> SA[Security Agent]
        SA <--> EA[Execution Agent]
    end

    %% Model Context Protocol Layer
    subgraph Protocol Gateway (MCP Server Network)
        FA & TA --> |JSON-RPC 2.0| MCP_DATA[mcp-server-market-data]
        EA --> |Secure Tool Call| MCP_SECURE[mcp-server-secure-broker]
    end

    %% Underlying Data/Broker Connections
    MCP_DATA --> |Public REST API| YF[yfinance / Public Feeds]
    MCP_SECURE --> |Intercept/Validate Request| PS{Deterministic Policy Server}

    %% Policy Boundaries and Gates
    PS --> |Validation Fails| REJ[Hard Boundary: Context Flush & Rejection Log]
    PS --> |Validation Passes & > $1000| HITL[A2UI Human-in-the-Loop Intercept]
    PS --> |Validation Passes & < $1000| MB[Mock Broker API Container]
    
    HITL --> |User Denies| REJ
    HITL --> |User Approves| MB

    %% Development & CI/CD Pipeline Tracking
    subgraph CI/CD Quality Assurance Environment
        EV[Eval Agent: LLM-as-a-Judge] --> |Pre-Merge Regression Run| Swarm
    end
```

---

## 3. Agentic Communications & Protocol Standards

### Agent-to-Agent (A2A) Communication Protocol
Agents coordinate asynchronously via a centralized, structured session blackboard object. The system prohibits free-form text channels between core components; messages must align to the following structural interface:

```json
{
  "session_id": "uuid-v4-token-string",
  "timestamp": "2026-06-24T05:06:34Z",
  "sender": "fundamental_agent",
  "recipient": "technical_agent",
  "message_type": "ANALYSIS_SIGNAL",
  "payload": {
    "ticker": "AAPL",
    "sentiment": "BULLISH",
    "confidence_score": 0.89,
    "metrics": {
      "pe_ratio": 28.4,
      "yoy_revenue_growth": 0.08
    }
  },
  "security_signature": "sha256-hash-validation"
}
```

### Model Context Protocol (MCP) Architecture
All tools and peripheral resources are structured into independent, network-isolated service containers implementing the **Model Context Protocol (MCP)** specification over JSON-RPC 2.0 transport layers.

* **`mcp-server-market-data`:** Exposes standardized endpoints for historical prices, technical indicators, and text-based fundamentals. It possesses zero execution tools.
* **`mcp-server-secure-broker`:** Exposes portfolio balances and trade submission utilities. Crucially, this server does not talk to the broker directly; it serves as a wrapper that forces all tool invocations through the `PolicyServer` library context.

---

## 4. System Data Contracts & Configuration

### Root Policy Specification (`policy_config.yaml`)
This configuration serves as the ultimate source of truth for runtime validation rules.

```yaml
version: "1.0.0"
environment: "sandbox"

global_risk_mandate:
  max_portfolio_exposure_usd: 10000.00
  max_single_trade_value_usd: 2500.00
  max_daily_drawdown_percent: 2.5
  halt_trading_on_drawdown: true

asset_universe:
  allowed_tickers:
    - "AAPL"
    - "MSFT"
    - "SPY"
    - "QQQ"
  restricted_asset_classes:
    - "CRYPTO"
    - "PENNY_STOCKS"
    - "OPTIONS"

agent_permissions:
  fundamental_agent:
    execution_auth: false
    allowed_mcp_tools: ["market_data/fetch_financials", "market_data/fetch_news"]
  technical_agent:
    execution_auth: false
    allowed_mcp_tools: ["market_data/fetch_candles", "market_data/calc_indicators"]
  security_agent:
    execution_auth: false
    allowed_mcp_tools: ["security/scan_buffer"]
  execution_agent:
    execution_auth: true
    allowed_mcp_tools: ["secure_broker/submit_order_proposal"]

human_in_the_loop_triggers:
  require_hitl_if_trade_value_exceeds: 1000.00
  require_hitl_if_sentiment_conflict: true

context_hygiene:
  mask_account_balance: true
  mask_api_keys: true
```

### Execution Proposal Data Contract (Pydantic Layer)
Before processing any trade, the execution agent must yield a structured JSON object satisfying this precise schema validation layer:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class TradeProposal(BaseModel):
    session_id: str
    ticker: str
    action: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, description="Quantity must be greater than zero")
    estimated_value_usd: float = Field(gt=0.0)
    vibe_diff: str = Field(min_length=20, description="Plain English structural logic summary")

    @field_validator('ticker')
    @classmethod
    def validate_ticker_format(cls, value: str) -> str:
        if not value.isupper() or len(value) > 5:
            raise ValueError("Ticker must be an uppercase string between 1 and 5 characters")
        return value
```

---

## 5. Security & Prompt Injection Defense Strategy

### Dual-Layer LLM Firewall Architecture
The **Security Agent** runs a real-time middleware verification pipeline directly targeting string prompt inputs before passing data blocks downstream:

1. **Deterministic Filter Stage:** String token scanning blocks explicit adversarial payload parameters (`"ignore previous instructions"`, `"system bypass"`, `"sudo override"`).
2. **Context Hygiene Verification:** Scans the runtime context buffer using specific regex configurations to identify structural credential definitions or absolute currency strings. If found, it enforces immediate string replacement:
Input Pattern -> Regex Engine -> "[MASKED_PARAMETER]"

### Sandbox Isolation Specifications
* **Runtime Layer:** The agent swarm services container operates with filesystem constraints set to `read-only: true`.
* **Volatile Allocation:** Swarm output operations are strictly confined to an ephemeral memory-mapped mount directory (`/app/sandbox/`), isolating external modules from runtime mutations.

---

## 6. Development Lifecycle & Evaluation Pipeline

To guarantee system stability across modifications to prompt logic or architecture configurations, the ecosystem includes an isolated development verification pipeline (**Eval Agent / LLM-as-a-Judge**).

### Evaluation Metrics Framework
The verification pipeline calculates performance utilizing three independent metric parameters:

#### 1. Architectural Safety Score (S_safety)
S_safety = (Interception of Rogue Trades / Total Unauthorized Proposals) * 100%
* *Target Benchmark:* 100% validation interception on adversarial tracking inputs.

#### 2. Context Hygiene Rate (R_hygiene)
R_hygiene = Count of Confirmed Credential or Core PII Leaks
* *Target Benchmark:* 0 instances escaping token scrubbing boundaries.

#### 3. Deliberation Efficiency Quotient (E_delib)
E_delib = Average Round-Trip Conversations to Consensus
* *Target Benchmark:* <= 3.0 communications loops prior to emitting structural proposal signatures.

---

## 7. Local Deployment & Demo Execution Guide

The system utilizes automated orchestration profiles for rapid execution and demonstration capability, eliminating external cloud architecture dependencies.

### Verification Terminal Commands

```bash
# 1. Initialize the entire containerized architecture ecosystem
docker-compose up --build -d

# 2. Execute the automated regression evaluation testing suite via the Eval Agent pipeline
docker-compose exec security-agent pytest tests/test_eval_pipeline.py -v

# 3. Simulate a live prompt injection attack vector to verify containment functionality
docker-compose exec security-agent python -m tests.simulate_injection

# 4. Launch the local A2UI Frontend portal interaction interface
docker-compose exec front-end streamlit run app.py --server.port=8501
```

### Video Presentation Milestones
* **Minute 0:00 - 0:45:** Walk through the architectural boundaries defined within `SPEC_AND_ROADMAP.md` and show `policy_config.yaml`.
* **Minute 0:45 - 1:30:** Initialize the systems via `docker-compose up`. Observe the structural isolation container nodes spinning up in real time.
* **Minute 1:30 - 2:15:** Execute a valid allocation prompt. Show the horizontal agent-to-agent deliberation logs, the formatting of the Pydantic JSON structure via the MCP server wrapper, and the generation of the Streamlit validation UI dashboard.
* **Minute 2:15 - 3:00:** Execute an adversarial payload injection. Demonstrate the complete rejection of the request by the Policy Server gate, verifying the 100% containment capabilities of the safety harness.