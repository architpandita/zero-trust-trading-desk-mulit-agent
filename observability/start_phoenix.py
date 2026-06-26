#!/usr/bin/env python3
"""
observability/start_phoenix.py
──────────────────────────────
Launches Arize Phoenix — a local, open-source observability UI for agent traces.

Usage:
    source venv/bin/activate
    python observability/start_phoenix.py

Phoenix UI → http://localhost:6006
Traces     → http://localhost:6006/v1/traces  (OTel HTTP endpoint)

The trading-desk orchestrator sends a span for every decision:
  trade.decision.EXECUTED
  trade.decision.PENDING_HITL
  trade.decision.REJECTED_INJECTION
  ... etc.

Each span carries these attributes you can filter/group by in the UI:
  trade.ticker            AAPL / MSFT / ...
  trade.decision_code     EXECUTED / REJECTED_POLICY / PENDING_HITL / ...
  trade.value_usd         Estimated trade value
  trade.consensus_match   true / false
  trade.pydantic_retries  0-3
  policy.passed           comma-joined list of checks that passed
  policy.failed           comma-joined list of checks that failed

Improvement workflow
────────────────────
1. Run some directives via the web UI (http://localhost:5173)
2. Open Phoenix (http://localhost:6006) → Traces tab
3. Filter spans where  trade.consensus_match = false
   → These are trades where agents disagreed.
   → Tune scenario_agents.py thresholds to fix systematic disagreements.
4. Filter spans where  trade.decision_code STARTS WITH REJECTED
   → High rejection rate on a ticker? Add it to the approved list in policy_config.yaml.
   → High REJECTED_INJECTION rate? Review the raw prompts — someone may be probing.
5. Sort by  trade.pydantic_retries DESC
   → High retry count = execution agent producing malformed proposals.
   → Improve the execution agent's output schema or parsing logic.
"""
import sys

def check_deps():
    missing = []
    try:
        import phoenix  # noqa: F401
    except ImportError:
        missing.append("arize-phoenix")
    try:
        import opentelemetry  # noqa: F401
    except ImportError:
        missing.append("opentelemetry-sdk")
    try:
        import opentelemetry.exporter.otlp.proto.http  # noqa: F401
    except ImportError:
        missing.append("opentelemetry-exporter-otlp")

    if missing:
        print("❌  Missing packages. Install them with:\n")
        print(f"    pip install {' '.join(missing)}\n")
        print("Then re-run:  python observability/start_phoenix.py")
        sys.exit(1)

check_deps()

import phoenix as px  # noqa: E402

print("=" * 60)
print("  Zero-Trust Trading Desk — Phoenix Observability")
print("=" * 60)
print()
print("  UI  →  http://localhost:6006")
print("  API →  http://localhost:6006/v1/traces  (OTel OTLP/HTTP)")
print()
print("  Send trading directives through the web UI and watch")
print("  spans appear here in real-time.")
print()
print("  Press Ctrl+C to stop.")
print("=" * 60)

# Launch Phoenix with its built-in OTLP collector
session = px.launch_app()
print(f"\n  Phoenix started: {session.url}")

# Block so the process stays alive
try:
    import time
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("\nPhoenix stopped.")
