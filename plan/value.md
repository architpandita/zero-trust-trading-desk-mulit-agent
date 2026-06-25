 Your submission should showcase both the vision behind your project and the technical decisions that bring it to life. Judges will evaluate projects based on their problem definition, solution design, implementation quality, effective use of agent technologies, and overall user value. Successful submissions will clearly demonstrate concepts covered in the course while highlighting thoughtful architecture, strong documentation, and a compelling project story.
To help you verify your capstone project against the learning objectives of the course, I have summarized the core skills and architectural standards taught across the four whitepapers.

### 1. **Day 1: The New SDLC with Vibe Coding**

This paper focuses on the transition from traditional, syntax-based development to **Agentic Engineering**, where developers focus on intent and orchestrate autonomous systems.

* **Key Skills & Concepts:**
* 
**Intent-Driven Development:** Shifting from writing raw syntax to expressing high-level intent, with the model handling the implementation.


* 
**Orchestration vs. Conductor Roles:** Developing the ability to act as a "conductor" (hands-on, real-time direction) or an "orchestrator" (async, multi-agent delegation).


* 
**Harness Engineering:** Building the surrounding infrastructure (constraints, tests, feedback loops) that allows agents to operate safely.


* 
**The Factory Model:** Viewing the software lifecycle as a system that produces software, requiring management of intent, architecture, and quality rather than just keystrokes.





### 2. **Day 2: Agent Tools & Interoperability**

This paper establishes the "Industry Standards" (protocols) required for agents to interact reliably with the world and each other.

* **Key Skills & Concepts:**
* 
**Protocol Adoption:** Learning to implement standard communication protocols to avoid bespoke, fragile wrappers.


* 
**MCP (Model Context Protocol):** "USB-C" for connecting models to data/filesystems.


* 
**A2A (Agent-to-Agent):** Standardized communication for delegation and negotiation.


* 
**A2UI (Agent-to-User Interface):** Turning complex JSON outputs into safe, interactive visual components (Generative UI).


* 
**AP2 & UCP (Commerce/Payment):** Secure autonomous transaction execution.




* 
**Modular Architecture:** Moving from isolated "custom machines" to plug-and-play platforms.





### 3. **Day 3: Agent Skills**

This paper introduces **Agent Skills** as a procedural memory primitive, allowing general-purpose agents to become specialists on demand without bloating their context.

* **Key Skills & Concepts:**
* 
**Procedural Memory:** Moving beyond episodic/semantic memory to teaching agents "how to do things step by step".


* 
**Skill Anatomy:** Learning the standard structure: a folder containing `SKILL.md`, `scripts/`, `references/`, and `assets/`.


* 
**Meta-Skills:** Designing agents capable of authoring, evaluating, and improving other skills (e.g., assisted authoring from traces).


* 
**Library Governance:** Strategies for distributed ownership of skill libraries across domain teams.





### 4. **Day 4: Vibe Coding Agent Security and Evaluation**

This paper focuses on operationalizing trust in non-deterministic systems through "safety harnesses" and rigorous evaluation.

* **Key Skills & Concepts:**
* 
**7-Pillar Security Architecture:** Implementing sandboxes, supply chain defense, identity management, and JIT (Just-In-Time) downscoping.


* 
**Red/Blue/Green Teaming:** Using specialized agents to attack (Red), monitor/analyze (Blue), and auto-refactor/quarantine (Green) the system.


* 
**Observability & The "Vibe Trajectory":** Auditing the agent’s internal reasoning to measure intent drift and trust decay.


* 
**Evaluation Frameworks:** Differentiating between security (did it stay in bounds?) and evaluation (is the output worth shipping?).





---

### How to use this for your Capstone:

To verify if your project is effectively utilizing this learning, ensure it demonstrates:

1. 
**Orchestration:** Does it use a clear "harness" or policy layer to govern agent actions? 


2. 
**Interoperability:** Does it use standard protocols (like MCP) rather than custom, fragile wrappers? 


3. 
**Procedural Memory:** Can your agent pull in specialist knowledge on demand via a skill structure rather than relying on a monolithic system prompt? 


4. 
**Trust & Eval:** Can you demonstrate an audit trail or "vibe trajectory" that shows *why* an agent made a decision, and is there a mechanism to catch intent drift?


Kaggle Capstone Alignment: The Business Case for Zero-Trust

To win the "Agents for Business" track, a project must transcend a "cool AI script" and demonstrate enterprise readiness. Businesses do not adopt AI that they cannot control, audit, or trust.

Here is the strategic breakdown of how our specific architectural features directly satisfy enterprise constraints and maximize the Capstone scoring rubric.

1. Model Context Protocol (MCP) Integration

What it is: Decoupling tools from the agents into isolated, standardized JSON-RPC protocol servers (e.g., mcp-server-secure-broker).

Capstone Requirement Met: Security & Enterprise Modularity. * The "Judge Flex": We eliminate "Ambient Authority." Agents are not given raw API keys. By forcing all actions through MCP, we prove to enterprise risk managers that the agent is physically sandboxed from the financial execution layer. It demonstrates cutting-edge adherence to open standards.

2. Agent-to-UI (A2UI) & Human-in-the-Loop (HITL)

What it is: A Streamlit dashboard that intercepts trades over $1,000, displaying a "Vibe Diff" and requiring a physical human click to approve.

Capstone Requirement Met: Usability & Risk Management.

The "Judge Flex": Most agentic projects end in a terminal. We built a Decision Support System. This proves we understand the end-user (a risk manager or portfolio manager). Enterprises require auditable human sign-offs; A2UI makes the agent a collaborative employee, not a rogue black box.

3. Parallel Agent-to-Agent (A2A) with Deterministic Consensus

What it is: Using asyncio to run the Fundamental and Technical agents simultaneously (Fork), and using a hard-coded Python script to merge their decisions (Join).

Capstone Requirement Met: Latency, Cost Efficiency & Reliability.

The "Judge Flex": Cyclic graph workflows (Think-Act-Observe) suffer from high latency and token bloat. By running agents in parallel and using deterministic logic to break ties, we drastically reduce API costs and execution time. It proves we know when to use LLMs (for reasoning) and when to use standard code (for logic gates).

4. Ephemeral State (Zero-Persistence Memory)

What it is: Purging the session_data RAM object immediately after the trade terminates. No databases, no historical context windows.

Capstone Requirement Met: Data Privacy & Context Hygiene.

The "Judge Flex": This solves the exact "context rot" and memory bloat blocker you faced in ADK 2.0. By making the system amnesiac, we immunize it against long-term prompt injection persistence. It guarantees every trade is evaluated strictly on current market data, passing stringent data-privacy compliance.

5. Automated Evaluation Pipeline (LLMOps / CI/CD)

What it is: The "Eval Agent" and Golden Dataset that tests the architecture for hallucinations and schema adherence before deployment.

Capstone Requirement Met: Maintainability & Scalability.

The "Judge Flex": This is the ultimate enterprise flex. It shifts the narrative from "I built a bot" to "I built an auditable software factory." It proves the system is robust against LLM model drift and can be safely maintained by a DevOps team.

6. Pydantic Contracts & Data Provenance

What it is: Forcing the Execution Agent to output strictly typed JSON that includes a cryptographic citation of the raw data used (DataProvenance).

Capstone Requirement Met: Auditability & Explainability.

The "Judge Flex": When the Policy Server evaluates a trade, it doesn't just trust the agent. The Provenance layer allows the system to verify the exact MCP data the agent looked at. This solves the "LLM hallucination" problem mathematically, providing the audit trail that financial regulators (SEC, FINRA) demand.

Summary for the Judges

This architecture does not just automate trading; it automates compliance. By wrapping non-deterministic reasoning engines (LLMs) in deterministic constraints (MCP, Pydantic, Policy Server, A2UI), we deliver the operational efficiency of Agentic AI without sacrificing the Zero-Trust security required by modern enterprises.

Based on the whitepaper **"Spec-Driven Production Grade Development in the Age of Vibe Coding" (Day 5)**, the document outlines specific engineering skills and methodological shifts required to transition from ad-hoc prototyping to production-grade, agentic software development.

To verify if your capstone project is aligned with these learning objectives, you can evaluate your work against the following skills and practices identified in the paper:

### 1. Spec-Driven Development (SDD) Skills

The core shift is from "Code-First" to "Spec-First" development.

* 
**Architectural Blueprinting:** The ability to write high-quality technical specifications in Markdown/YAML that serve as the "source of truth" for both humans and AI.


* 
**Behavior-Driven Development (BDD) Syntax:** Using the Gherkin **Scenario / Given / When / Then** structure to describe system behavior. This forces the agent to follow a strict logical track rather than guessing.


* 
**Format Optimization:** Designing specifications to be lean and token-efficient. This includes utilizing a hybrid approach: **Markdown** for narrative instructions and **flat YAML blocks** for structured data/schemas to ensure maximum parsing accuracy.



### 2. Interaction & Integration Skills

* 
**Orchestration via Spec Folders:** Organizing projects such that the agent dynamically indexes a `specs/` directory rather than relying on massive, fragmented chat prompts.


* 
**MCP (Model Context Protocol) Implementation:** Building MCP servers to provide agents with standard, secure access to data (e.g., SQLite databases or APIs) without needing custom, brittle integrations.


* 
**Context Management:** Practicing "Context Hygiene" by keeping instructions in appropriate layers (Global Profiles, Shared Multi-Tool `AGENTS.md`, and Project-specific specs) rather than dumping data into ephemeral chat sessions.



### 3. Execution & Debugging Modes

The paper categorizes development tasks into specific "Execution Modes" that require different prompting strategies:

* **The Architect (Project Generation):** Scaffolding projects without "YOLO mode" (coding immediately); requiring confirmation of folder structure, tech stack, and test/logging plans first.
* **The Builder (Feature Generation):** Matching existing style, naming patterns, and error handling in existing codebases.
* **The Forensic Specialist (Bug Fixing):** Shifting from "Symptom Prompting" to **Evidence Prompting** (e.g., providing specific error logs) and setting strict constraints to fix only the root cause.
* **The Librarian (Data Engineering):** Using cloud extensions (e.g., Google Cloud Data Extension) to query data and requiring the agent to display the specific SQL/command used.

### 4. Operational Guardrails & Quality Assurance

* 
**Automated Verification:** Leveraging AI to generate comprehensive test coverage and using built-in browser tools (like in Antigravity) to autonomously verify visual fixes in a sandboxed environment.


* 
**Human-in-the-Loop (HITL) Reviews:** Transitioning human oversight from "nitpicking style" to "ensuring architectural integrity".


* 
**Code Review Automation:** Building "Skills" that automate initial security/logic reviews for Pull Requests, such as checking for hardcoded secrets, SQL injection, and logic errors before a human reviewer looks at the code.



---

### Verification Checklist for Your Capstone:

* [ ] **Does your project have a dedicated `specs/` folder?** (Are your instructions stored in structured Markdown/YAML files rather than buried in chat?)
* [ ] **Are you using a deterministic spec format?** (e.g., Does it utilize BDD "Given/When/Then" scenarios for critical logic?)
* [ ] **How does the agent access external data?** (Does it use a standard protocol like MCP, or are you hardcoding connections?)
* [ ] **Is there a "Security/Review" skill implemented?** (Does your agent automatically check its own PRs/commits for critical vulnerabilities or logic flaws as suggested in the snippet on Code Reviews?)