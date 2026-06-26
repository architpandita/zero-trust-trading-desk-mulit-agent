# Zero-Trust Multi-Agent Trading Desk

> *"The only AI trading system where the agents themselves are not trusted."*

---

## ⚡ Quick Pitch
AI agents fail, hallucinate, and are vulnerable to prompt injections. The **Zero-Trust Multi-Agent Trading Desk** is a defensive trading architecture designed to run untrusted AI swarms securely. By applying zero-trust network principles to LLMs, we strip agents of "ambient authority" (broker keys) and route every trade proposal through a deterministic, math-first Python **Policy Server** and **Human-in-the-Loop (HITL) Queue**. If the AI is jailbroken or goes rogue, the system fails closed.

## 📖 The Storyline
Priya, a quant researcher, lost three months of gains when her firm's new AI assistant hallucinated and executed an unauthorized $47,000 buy order. The post-mortem revealed a critical design flaw: *ambient authority*. The AI held the API keys, believed its own hallucinations, and acted directly. Priya set out to rebuild the system from scratch with one core rule: **Treat AI agents like untrusted code in a sandboxed environment.**

## 🎯 Key Assumptions
1. **Agents Will Fail**: We assume LLM agents *will* hallucinate, err, or suffer adversarial prompt injections.
2. **Zero Ambient Authority**: Agents must *never* hold API keys or trade credentials. They only output proposals.
3. **Deterministic Enforcement**: Safety cannot be delegated to an LLM. Policy gates must be hard-coded, math-driven, and cryptographic.
4. **Data Provenance**: Every piece of data used to make a trade decision must be cryptographically hashed and verified against the source.

## 🚀 What to Expect
- **Specialized Multi-Agent Swarm**: A collaborative crew of Fundamental, Technical, and Execution agents working in a bounded context.
- **Fail-Closed Consensus**: Deterministic consensus matching ensuring trades are blocked if agents disagree.
- **Human-in-the-Loop Triggers**: Automatic routing of trades over $1,000.00 or with sentiment conflict to a queue for approval/denial.
- **Crypto Data Integrity**: SHA256 hashing to verify that execution parameters match market data fetched at the start of the session.
- **Sleek Reactive UI**: A modern dashboard showing real-time console messages, a pending HITL review queue, trade history, and masked portfolio stats that persist across page reloads.

---

## What This System Does

The system coordinates a swarm of specialized AI agents to analyze stocks, reach consensus, and propose trades — all within a strict zero-trust boundary that prevents any single agent from causing financial harm.

**A session looks like this:**

```
Priya types:  "Analyze AAPL. Should we enter a position today?"

[Layer 1]  Security Middleware scans the prompt.
           ✅ No injection patterns. No PII. Passes.

[Layer 2]  Orchestrator forks two agents in parallel (30s hard limit):
           📊 Fundamental Agent  →  PE ratio, earnings, news sentiment
           📈 Technical Agent    →  SMA crossover, RSI, volume signals

[Layer 3]  Deterministic Consensus Gate (pure Python, no LLM):
           Both agents return BULLISH
           ✅ Consensus: MATCH. Proceeding.

[Layer 4]  Execution Agent proposes a TradeProposal (Pydantic-validated):
           Ticker: AAPL | Action: BUY | Qty: 5 | Value: $752.50
           SHA256 hash of market data attached.

[Layer 5]  Policy Server validates (no LLM, reads policy_config.yaml):
           ✅ Ticker in allowed universe
           ✅ Value ≤ $2,500 max
           ✅ Hash matches source data
           📋 Value > $1,000 → routes to Human-in-the-Loop queue

[Layer 6]  HITL Dashboard shows Priya the trade card:
           "AAPL BUY · $752.50 · Both agents BULLISH · Data hash verified"
           [APPROVE] [DENY]

Priya clicks APPROVE. The order is submitted. The audit log is written.
Session data is purged from RAM. The system forgets everything.
```

Nobody held API keys but the Policy Server. No trade was executed without a human seeing it. No data was used without a cryptographic citation.

This is what it means to trust nobody.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER DIRECTIVE (Priya's Prompt)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ LAYER 1: INGEST │  scan_ingest()
                    │ Security Filter │  Regex firewall
                    │   (Middleware)  │  PII masking
                    └────────┬────────┘
                             │ clean prompt
          ┌──────────────────┼──────────────────┐
          │                  │                  │
 ┌────────▼────────┐         │        ┌─────────▼───────┐
 │  FUNDAMENTAL    │         │        │   TECHNICAL     │
 │     AGENT       │  asyncio│        │     AGENT       │
 │  (PE, earnings  │  .gather│        │  (SMA, RSI,     │
 │   news, macro)  │  30s    │        │   volume,       │
 └────────┬────────┘  timeout│        │   momentum)     │
          │                  │        └─────────┬───────┘
          └──────────────────┼──────────────────┘
                             │ AnalysisSignal × 2
                    ┌────────▼────────┐
                    │ LAYER 3:        │
                    │ CONSENSUS GATE  │  deterministic_consensus_gate()
                    │ (Pure Python)   │  Fail-Closed: conflict → ABORT
                    └────────┬────────┘
                             │ ConsensusResult
                    ┌────────▼────────┐
                    │ EXECUTION AGENT │  TradeProposal (Pydantic)
                    │ (Proposal Draft)│  SHA256 data provenance
                    │  max 3 retries  │  SCHEMA_ABORT on failure
                    └────────┬────────┘
                             │ TradeProposal
                    ┌────────▼────────┐
                    │ LAYER 5:        │
                    │ POLICY SERVER   │  Deterministic Python
                    │ (Zero-LLM Gate) │  Reads policy_config.yaml
                    │                 │  Hard limits: ticker, size, hash
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐ ┌────▼──────┐ ┌────▼──────────┐
    │  EXECUTED      │ │PENDING    │ │  REJECTED_*   │
    │  Auto-approved │ │HITL Queue │ │  Hard abort   │
    │  ≤ $1,000      │ │> $1,000   │ │  No appeal    │
    └────────────────┘ └─────┬─────┘ └───────────────┘
                             │
                    ┌────────▼────────┐
                    │   HITL          │
                    │   DASHBOARD     │  Streamlit / FastAPI
                    │  (Priya's UI)   │  APPROVE / DENY
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   AUDIT LOG     │  Immutable event log
                    │  TELEMETRY      │  No PII · hashes only
                    │  Health Score   │  S_safety · R_hygiene · E_delib
                    └─────────────────┘
```

---

## Key Design Decisions

### 1. Agents Are Untrusted by Architecture, Not by Policy

In most AI systems, safety is a *policy* — a set of rules the AI is asked to follow. Policies can be prompted away. In this system, agents are architecturally incapable of executing trades. They can only produce `AnalysisSignal` and `TradeProposal` Pydantic objects. The actual execution endpoint is behind a Policy Server the agents have no access to.

### 2. The Policy Server Has No LLM

This is the most important decision in the system. The policy server is ~50 lines of deterministic Python. It reads a YAML file. It does arithmetic. An LLM cannot talk it out of a decision.

```yaml
# config/policy_config.yaml
global_risk_mandate:
  max_single_trade_value_usd: 2500.00
  max_daily_drawdown_percent: 2.5

human_in_the_loop_triggers:
  require_hitl_if_trade_value_exceeds: 1000.00
```

### 3. Cryptographic Data Provenance

Every piece of market data returned by the MCP servers carries a SHA256 hash computed from the raw payload. The `TradeProposal` must cite this hash. The Policy Server recomputes it. If they don't match — the agent hallucinated or altered the data — the trade is rejected as `REJECTED_HASH_MISMATCH`. Mathematically, you cannot fake a cited source.

### 4. Fail-Closed Consensus

When the Fundamental Agent says BULLISH and the Technical Agent says BEARISH, the system does not ask a third agent to break the tie. It immediately returns `REJECTED_CONSENSUS`. This is the "fail-closed" principle: uncertainty is treated as danger.

### 5. Ephemeral State

Every session is a completely isolated, in-memory context. When a session ends — for any reason, including failure — all session data is purged from RAM in a `finally` block. The system cannot accumulate context across sessions. An attacker who compromises one session gets nothing from previous ones.

---

## System Invariants (The Constitution)

These rules are enforced at the code level, not the policy level. They cannot be "prompted away":

| # | Rule | How Enforced |
|:--|:--|:--|
| I-1 | No agent holds API keys | Agents have no import of broker credentials |
| I-2 | Policy Server uses no LLM | Pure Python/Pydantic, no model call |
| I-3 | All broker calls go through Policy Server | Architecture — no direct broker import in agent code |
| I-4 | Session data purged on termination | `finally` block in `run_swarm_session` |
| I-5 | Consensus uses deterministic Python | `deterministic_consensus_gate()` is a pure function |
| I-6 | Every MCP response has SHA256 hash | Enforced in `hash_utils.generate_data_hash()` |
| I-7 | Agents bounded by 30-second timeout | `asyncio.wait_for(..., timeout=30.0)` |
| I-8 | Telemetry logs no PII | Allow-list in `telemetry._strip_pii()` |

---

## Test Coverage

The system was built entirely test-first (TDD). Every invariant has a corresponding test:

```
tests/
├── test_phase1_security.py          # 5  tests  — Injection filter, PII masking
├── test_phase1_schemas.py           # 7  tests  — Pydantic schema validation
├── test_phase1_policy_server.py     # 6  tests  — Policy gate hard limits
├── test_phase2_mcp_market_data.py   # 4  tests  — Market data + hash integrity
├── test_phase2_mcp_broker.py        # 3  tests  — Broker API + balance masking
├── test_phase3_consensus.py         # 3  tests  — Consensus gate logic
├── test_phase3_orchestrator.py      # 5  tests  — State machine, timeout, semaphore
├── test_phase4_state_manager.py     # 6  tests  — HITL API + audit + health
├── test_eval_pipeline.py            # 10 tests  — Golden dataset (CI/CD gate)
└── test_injection_simulator.py      # 1  test   — Adversarial attack simulation

Total: 50 tests · 0 failures · 1 warning (deprecation)
```

**The 10 Golden Dataset test cases are the CI/CD merge gate.** No code reaches `main` without all 10 passing.

---

## Project Structure

```
zero-trust-trading-desk-multi-agent/
│
├── agents/
│   ├── security/
│   │   └── middleware.py          # Layer 1 — scan_ingest(), InjectionDetectedError
│   ├── orchestrator/
│   │   ├── orchestrator.py        # 8-state machine, asyncio.gather, Semaphore(5)
│   │   ├── consensus.py           # deterministic_consensus_gate() — pure Python
│   │   └── telemetry.py           # async emit_event_log() — fire-and-forget
│   ├── execution/
│   │   └── schemas.py             # TradeProposal, AnalysisSignal, EventLog (Pydantic)
│   ├── shared/
│   │   └── exceptions.py          # ConsensusFailError
│   └── eval/
│       └── scenario_agents.py     # Directive-driven agents for eval pipeline
│
├── mcp/
│   ├── market_data/
│   │   ├── main.py                # FastAPI — /fetch_financials, /fetch_candles
│   │   ├── data_service.py        # Ticker allow-list + mock data
│   │   └── hash_utils.py          # generate_data_hash() — shared SHA256 utility
│   └── broker/
│       ├── main.py                # FastAPI — /submit_order_proposal, /portfolio
│       ├── policy_server.py       # PolicyServer — deterministic, no LLM
│       └── mock_kite.py           # Mock Kite Connect API (orders, trades, holdings)
│
├── api/
│   └── state_manager/
│       ├── main.py                # FastAPI — /pending, /decision, /audit, /health
│       ├── models.py              # Pydantic models for HITL + audit
│       └── audit.py               # In-memory audit store + health score calculation
│
├── config/
│   └── policy_config.yaml         # All risk limits (never in agent context)
│
└── tests/
    ├── conftest.py                # Shared fixtures
    ├── simulate_injection.py      # Adversarial injection simulator
    └── test_*.py                  # 50 tests across 5 phases
```

---

## The Decision Codes

Every session terminates with exactly one of these codes:

| Code | Meaning | Triggered by |
|:--|:--|:--|
| `EXECUTED` | Trade auto-approved and submitted | Value ≤ $1,000, all checks pass |
| `PENDING_HITL` | Waiting for human decision | Value > $1,000, all checks pass |
| `APPROVED_HITL` | Human approved the trade | Operator clicks APPROVE |
| `DENIED_HITL` | Human denied the trade | Operator clicks DENY |
| `REJECTED_INJECTION` | Prompt injection detected | Layer 1 firewall |
| `REJECTED_CONSENSUS` | Agents disagree | Deterministic gate, Fail-Closed |
| `REJECTED_POLICY` | Policy hard limit violated | Ticker, asset class, or size |
| `REJECTED_HASH_MISMATCH` | Data provenance failure | Hallucinated or tampered hash |
| `SCHEMA_ABORT` | Pydantic validation failed 3× | Execution agent cannot produce valid proposal |
| `TIMEOUT` | Agent exceeded 30s | asyncio.wait_for |

---

## Tech Stack

| Layer | Technology | Why |
|:--|:--|:--|
| Language | Python 3.11 | asyncio native, Pydantic v2 |
| API Framework | FastAPI | Async, auto-validated with Pydantic |
| Schema Validation | Pydantic v2 | Hard type enforcement at every boundary |
| Policy Config | PyYAML | Human-readable, version-controlled limits |
| Concurrency | asyncio | Non-blocking Fork/Join, Semaphore(5) |
| Testing | pytest + pytest-asyncio | TDD, RED-GREEN-REFACTOR throughout |
| Data Integrity | hashlib SHA256 | Cryptographic provenance on every MCP response |
| Mock Broker | FastAPI (Kite-style) | Realistic order/trade/portfolio simulation |

---

## Who This Is For

- **Quantitative researchers** who want to know the AI's thesis *before* it acts
- **Risk managers** who need a paper trail for every execution decision
- **AI engineers** who are building autonomous financial agents and are scared of what they've built
- **Regulators** who want to know: *"Can this system be manipulated by a clever prompt?"* — and want the answer to be: *"No. We checked. Here are 50 tests."*

---

## Contributing

The 10 Golden Dataset tests in `tests/test_eval_pipeline.py` are the specification. If you want to add a feature, write a failing GD test first. Then implement. Then submit.

---

*Built with the belief that the most important property of an AI financial system is not intelligence — it's accountability.*
