# ROADMAP.md: Execution & Kaggle Submission Plan

## Phase 1: Foundation & Security Core (Days 1–3)
*Goal: Establish the deterministic boundaries and container scaffolding before introducing any LLM logic.*

- [ ] **System Contracts:** Finalize `policy_config.yaml` and the Pydantic `TradeProposal` schema.
- [ ] **Infrastructure Setup:** Create the `docker-compose.yaml` to define network boundaries for the Swarm, MCP servers, and UI.
- [ ] **Deterministic Policy Server:** Build the Python core that ingests the YAML config and exposes a validation endpoint.
- [ ] **Security Agent (Stage 1):** Implement the regex-based context hygiene scanner and token-stripping middleware.

## Phase 2: The Protocol Gateway (Days 4–6)
*Goal: Build the isolated data and execution tools using the Model Context Protocol (MCP).*

- [ ] **Public Data MCP:** Build `mcp-server-market-data`. Implement read-only tools for `fetch_financials` and `fetch_candles` using `yfinance` or mock data.
- [ ] **Secure Broker MCP:** Build `mcp-server-secure-broker`. Implement the `submit_order_proposal` tool and **hard-wire it to the Policy Server**.
- [ ] **Protocol Testing:** Verify locally that calling the Broker MCP with an oversized trade is successfully blocked by the Policy Server.

## Phase 3: Agent Swarm & A2A Deliberation (Days 7–9)
*Goal: Breathe life into the agents and establish their horizontal communication network.*

- [ ] **A2A Blackboard:** Build the Swarm Orchestrator session state (the JSON log where agents post their analysis).
- [ ] **Specialized Prompts:** Draft the system instructions for the Fundamental and Technical agents, constraining them to use only the Public Data MCP.
- [ ] **Execution Agent Engine:** Prompt the Execution agent to read the Blackboard and strictly output the Pydantic JSON schema to the Secure Broker MCP.
- [ ] **Security Agent (Stage 2):** Connect the Security Agent to monitor the A2A Blackboard for prompt injection attempts in real time.

## Phase 4: A2UI & Automated Evaluation (Days 10–12)
*Goal: Build the enterprise dashboard and the CI/CD testing pipeline.*

- [ ] **Human-in-the-Loop Intercept:** Update the Policy Server to dump flagged proposals into a `pending_approval.json` queue rather than using standard CLI inputs.
- [ ] **A2UI Portal:** Build the Streamlit frontend (`app.py`) to read the pending queue, display the "Vibe Diff," and provide the human Approval/Rejection buttons.
- [ ] **Eval Agent CI/CD:** Create `eval_pipeline.py` and the 10-question "Golden Dataset" to test the swarm for hallucinations and format adherence.

---

## Phase 5: Kaggle Packaging & Final Submission (Days 13–14)
*Goal: Translate the local Docker architecture into a winning Kaggle submission format tailored for the "Agents for Business" track.*

### Step 5.1: Create the Kaggle Notebook (`submission.ipynb`)
Because Kaggle kernels cannot natively run complex multi-container `docker-compose` setups, your notebook must act as an **Evaluation Report Generator**.
- [ ] **Cell 1 (Setup):** Clone your GitHub repository into the Kaggle environment and install dependencies (`pip install -r requirements.txt`).
- [ ] **Cell 2 (Display Contracts):** Print your `policy_config.yaml` to the notebook output so judges immediately see the Zero-Trust constraints.
- [ ] **Cell 3 (Run Eval Pipeline):** Execute your `eval_pipeline.py` script directly in the notebook. Output the final scores (100% Safety, 0% Hallucination, 100% Format Adherence).
- [ ] **Cell 4 (Trace Output):** Print a raw A2A deliberation log from a successful test run to prove the multi-agent communication works.

### Step 5.2: Write the Kaggle "Writeup" (The Business Case)
The Kaggle discussion post/writeup is often graded as heavily as the code. Structure it with these headers:
- [ ] **Problem Statement:** Explain "Ambient Authority" and why businesses are terrified to deploy LLM agents.
- [ ] **Our Solution:** Introduce the "Zero-Trust Trading Desk" with deterministic validation.
- [ ] **Innovation (The Flex):** Highlight the Model Context Protocol (MCP) isolation, the LLM-as-a-Judge Eval pipeline, and the Streamlit Agent-to-UI (A2UI) dashboard.
- [ ] **Return on Investment (ROI):** Explain how this architecture reduces compliance risk to near-zero while automating 80% of the quantitative deliberation process.

### Step 5.3: Record the 3-Minute Demo Video
Upload this to YouTube and embed it at the top of your Kaggle Writeup.
- [ ] **0:00 - 0:45:** Show the Architecture Diagram and the `policy_config.yaml`.
- [ ] **0:45 - 1:45 (Scenario A):** Run the system locally. Show the terminal logs of agents talking, then switch to the Streamlit UI to physically click the "Approve" button on a safe trade.
- [ ] **1:45 - 2:30 (Scenario B):** Paste a malicious Prompt Injection attack into the system. Show the Policy Server catching it and terminating the run.
- [ ] **2:30 - 3:00:** Show the Eval pipeline running and passing all tests.

### Step 5.4: Finalize Repository Documentation
Ensure your linked GitHub repository is pristine for judges who want to dig deeper.
- [ ] `README.md`: High-level overview, quickstart instructions (`docker-compose up`), and a link to the Kaggle notebook.
- [ ] `ARCHITECTURE_E2E.md`: The detailed markdown file explaining the MCP and A2A flows.
- [ ] `policy_config.yaml`: Clearly visible in the root directory.