This file serves as your **Project Charter**. Keeping this as a `CONTEXT.md` in your repository will ensure that your development stays aligned with the "Zero-Trust" architectural vision and keeps you on track for a winning Kaggle submission.

---

# CONTEXT.md: Trading Agent Harness (Zero-Trust Framework)

## 1. Project Overview

The **Trading Agent Harness** is a production-grade, multi-agent framework designed to govern autonomous financial agents. It shifts the paradigm from "experimental trading" to "auditable, governed financial operations."

## 2. Why This Project? (The "Winning" Narrative)

* **Problem:** Autonomous AI agents in finance suffer from "Ambient Authority" and lack of deterministic safety.
* **Solution:** A Zero-Trust architecture where no agent has native permission to execute trades. Every action is mediated by an independent **Policy Server**.
* **Competitive Edge:** Unlike standard trading bots, this project treats the "AI Agent" as an untrusted entity, focusing on **governance, risk-interception, and deterministic safety**—key requirements for production-grade enterprise software.

## 3. Key Architectural Pillars (The "Flex")

* **Zero-Trust Policy Engine:** Deterministic YAML-based guardrails (e.g., exposure limits, volatility gates) that intercept and audit every trade request.
* **Multi-Agent Deliberation Swarm:** Agents (Fundamental, Technical, Risk) deliberate on a signal; the system only executes if consensus meets safety mandates.
* **Context Hygiene:** Dynamic PII masking and session-based scoping ensure LLMs never access unauthorized account data.
* **Infrastructure-as-Code (IaC):** The project is designed for local reproducibility via `docker-compose`, eliminating the need for expensive cloud hosting while proving deployment readiness.

## 4. Crucial Implementation Constraints

* **Zero-Trust = No Ambient Authority:** Agents hold no API keys. All interactions with external services must pass through the `PolicyServer` middleware.
* **"Mock" over "Live":** To avoid costs and latency, the core demo will use a "Mock Broker API" container. This makes the project 100% reproducible for judges without requiring them to pay for market data.
* **Deterministic Safety:** The Policy Server must be written in standard, deterministic code (Python/Pydantic), not LLM-based logic. This proves to judges you understand how to control AI behavior.

## 5. Winning Criteria (Focus Areas)

* **Documentation:** High-quality `README.md` and `CONTEXT.md` to demonstrate professional engineering standards.
* **Modular Architecture:** Clear separation between the "Agent Brain" (LLM logic) and the "Governance Harness" (Policy Server/Middleware).
* **Reproducibility:** A single `docker-compose up` command must demonstrate the full workflow, from deliberation to intercepted trade.
* **Video Demo:** The 5-minute video must clearly show:
1. The agents debating a trade.
2. The **Policy Server rejecting a rogue trade** (proving the guardrail works).
3. Human-in-the-loop (HITL) authorization for a valid trade.



## 6. Development Workflow

1. **Notebook First:** Develop and test the core components (Policy Server + Agent Swarm) in a Kaggle notebook.
2. **Infrastructure Polish:** Move the code to the repository structure and add the `docker-compose` setup.
3. **Documentation & Writeup:** Finalize the narrative for the *Agents for Business* track, emphasizing the "Safety Harness" aspect.

---

**Pro-Tip:** You can save this file as `CONTEXT.md` in your root folder. Whenever you feel "feature creep" or start getting distracted by the complexity of the agents, refer back to this file to remind yourself: **"Am I focusing on the Governance and the Harness, or am I just chasing a better trading strategy?"**

Shall we start the "Notebook First" phase by outlining the **Policy Server's YAML schema**?