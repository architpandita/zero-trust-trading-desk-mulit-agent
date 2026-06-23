This project roadmap follows the "Notebook-First" strategy we discussed, focusing on architectural purity and the "Zero-Trust" framework to maximize your score in the *Agents for Business* track.

Save the following as `ROADMAP.md` in your repository.

---

# ROADMAP.md: Zero-Trust Trading Desk

## Phase 1: Architectural Scaffolding (Days 1–3)

*Goal: Establish the governance layer (the "Harness") before building the agents.*

* [ ] **Define Policy Schema:** Create the `policy_config.yaml` specifying trade constraints (e.g., max position size, volatility thresholds).
* [ ] **Implement Policy Server:** Develop the `PolicyServer` module in Python. This must act as a deterministic gatekeeper that returns `ALLOW` or `DENY` based on inputs.
* [ ] **Data Interface:** Build the `MarketDataAdapter` (interface for `yfinance` or mock feeds) to ensure the system is decoupled from specific data sources.
* [ ] **Environment Setup:** Create the `docker-compose.yaml` file to orchestrate the Policy Server, a Mock Broker API, and the core Agent container.

## Phase 2: Agent Swarm & Deliberation (Days 4–7)

*Goal: Build the "Brains" that operate within your safety harness.*

* [ ] **Define Agent Roles:** Draft system prompts for the three core agents:
* *Fundamental Agent* (Analyzes P/E, revenue, trends).
* *Technical Agent* (Analyzes RSI, moving averages, etc.).
* *Risk Agent* (The "Critic" that checks the Policy Server mandates).


* [ ] **Implement Deliberation Logic:** Build the orchestration loop where agents propose a trade and the Risk Agent/Policy Server validates it.
* [ ] **Context Hygiene Layer:** Implement a middleware that strips sensitive account/PII data from the LLM prompt stream.

## Phase 3: Testing, Safety, & HITL (Days 8–11)

*Goal: Prove "Zero-Trust" by attempting to "break" the system.*

* [ ] **Red Teaming (The "Vibe" Test):** Attempt to prompt-inject the agents into placing unauthorized trades.
* [ ] **HITL Integration:** Build the Human-in-the-Loop override mechanism. Ensure the agent provides a "Vibe Diff" (plain-English summary of reasoning) for human sign-off.
* [ ] **Mock API Validation:** Ensure your Mock Broker logs "Successful Trades" vs. "Rejected Attempts" clearly for the judges to see.

## Phase 4: Packaging & Submission (Days 12–14)

*Goal: Documentation that speaks "Enterprise" to the judges.*

* [ ] **Finalize README.md:** Highlight the Zero-Trust architecture and reproducible local setup.
* [ ] **Record Demo Video:** (Target: < 3 mins)
* Show the Agent Swarm discussing a trade.
* Show the Policy Server *blocking* an unauthorized trade.
* Show the human approving a valid trade.


* [ ] **Submit:** Finalize the Kaggle Writeup using the "Executive Summary" and architectural diagrams we prepared.

---

### Pro-Tips for Submission

* **Keep it clean:** The judges value "Thoughtful Architecture" (50 points). Your `PolicyServer` logic is the most important piece of code in the repo.
* **The "Why":** In your writeup, emphasize that you chose the *Agents for Business* track because financial markets are the ultimate high-stakes environment where "ambient authority" for AI is a critical vulnerability.
* **Documentation:** Ensure every class and major function has a docstring. Judges *will* look at your code quality.

[Kaggle AI Agents Capstone Project Explained](https://www.youtube.com/watch?v=euWWL4qji-E)

This video provides a comprehensive breakdown of the submission requirements and the evaluation rubric, which is helpful to keep in mind as you progress through each phase of the roadmap.