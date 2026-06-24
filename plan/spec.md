# SYSTEM_SPEC.md: Technical Specification & Governance

## 1. Executive Summary
The **Zero-Trust Trading Desk** is a headless, event-driven multi-agent framework. It operates without persistent storage, enforcing security through deterministic policy gates and automated data provenance.

## 2. Orchestrator State Machine (Parallel Fork-Join)
The system utilizes an `asyncio` parallel execution pattern to maximize throughput while maintaining absolute state separation.

* **State 0 (INIT):** Instantiate ephemeral `session_data` (RAM-only).
* **State 1 (PARALLEL_EXEC):** `Fork` Fundamental & Technical agents via `asyncio.gather` with a **30-second global timeout**.
* **State 2 (DETERMINISTIC_GATE):** Orchestrator executes a hard-coded tie-break logic (No LLM involvement).
* **State 3 (EXECUTION_PROPOSAL):** Execution Agent generates the JSON proposal using a 3-retry Pydantic validation loop.
* **State 4 (POLICY_GATE):** Policy Server verifies `TradeProposal` against `policy_config.yaml`.
* **State 5 (MONITORING & FEEDBACK):** Telemetry data (latency, decision accuracy, Pydantic failure count) is pushed to the `Eval Agent` pipeline for iterative improvement.
* **State 6 (TERMINATION):** Purge RAM, close session.

## 3. Monitoring & Feedback Architecture
To enable continuous improvement without a traditional database, the system implements a **Telemetry Sidecar**:
* **Telemetry Streaming:** During State 5, the Orchestrator emits an `EventLog` (JSON) to an ephemeral `telemetry_stream.log` file.
* **Performance Metrics:** The log tracks: 
    * Agent deliberation time (ms).
    * Pydantic retry count (detects prompt drift).
    * Consensus match rate (identifies if agents are getting confused).
* **Eval Agent Integration:** The `Eval Agent` runs a daily cron job to ingest `telemetry_stream.log`, calculating the "System Health Score" and suggesting prompt updates to fix recurring Pydantic errors.



## 4. Communication & Concurrency
* **A2A Communication:** Message passing via synchronous `session_data` dictionary objects.
* **Concurrency Control:** Orchestrator maintains sole control of state; `asyncio.Semaphore(5)` limits active sessions.
* **Error Handling:** `DataIntegrityError` triggers session abort and telemetry capture.

## 5. Data Provenance & Security
* **Provenance:** Proposals include the `DataProvenance` schema, linking trades to specific MCP tool inputs.
* **Injection Defense:** Deterministic regex scanning + Pydantic structural validation.
* **Zero-Persistence:** No database; logs are ephemeral.

## 6. System Constitution (`policy_config.yaml`)
*All proposed trades must be validated against the following:*

| Constraint Category | Rule | Action on Violation |
| :--- | :--- | :--- |
| **Max Trade Value** | > $2,500.00 | **REJECT** |
| **HITL Threshold** | > $1,000.00 | **PENDING_A2UI_APPROVAL** |
| **Sentiment** | Fundamental $\neq$ Technical | **REJECT** |
| **Asset Class** | Crypto/Options | **REJECT** |

## 7. Implementation Lifecycle
1.  **Foundation:** Docker Scaffolding & Policy Server logic.
2.  **MCP Gateway:** Developing `mcp-server-market-data` & `mcp-server-secure-broker`.
3.  **Swarm Intelligence:** Prompt engineering for FA/TA/EA agents.
4.  **Telemetry:** Implementing the Telemetry Sidecar & Eval Agent cron.
5.  **UI/UX:** Streamlit A2UI for HITL approval.
6.  **QA:** CI/CD Golden Dataset validation.