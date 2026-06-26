#!/usr/bin/env bash
# observability/query_audit.sh
# ─────────────────────────────
# Quick jq queries against logs/audit.jsonl for agent improvement analysis.
# Usage:  bash observability/query_audit.sh [command]
#
# Requires: jq  (brew install jq)

LOG="logs/audit.jsonl"

if [ ! -f "$LOG" ]; then
  echo "No audit log found at $LOG — run some directives first."
  exit 1
fi

CMD="${1:-summary}"

case "$CMD" in

  summary)
    echo "═══════════════════════════════════════"
    echo "  Audit Summary"
    echo "═══════════════════════════════════════"
    echo ""
    echo "── Decision Code Counts ────────────────"
    jq -r '.decision_code' "$LOG" | sort | uniq -c | sort -rn
    echo ""
    echo "── Tickers Seen ────────────────────────"
    jq -r 'select(.ticker != null and .ticker != "N/A") | .ticker' "$LOG" | sort | uniq -c | sort -rn
    echo ""
    echo "── Consensus Miss Rate ─────────────────"
    TOTAL=$(wc -l < "$LOG")
    MISS=$(jq -r 'select(.consensus_match == false) | .decision_code' "$LOG" | wc -l)
    echo "  $MISS / $TOTAL decisions had consensus_match=false"
    ;;

  rejections)
    echo "── All Rejections ──────────────────────"
    jq 'select(.decision_code | startswith("REJECTED"))' "$LOG"
    ;;

  consensus-misses)
    echo "── Consensus Failures (agents disagreed) ──"
    jq 'select(.consensus_match == false)' "$LOG"
    ;;

  hitl)
    echo "── HITL Decisions ──────────────────────"
    jq 'select(.decision_code == "PENDING_HITL" or .decision_code == "APPROVED_HITL" or .decision_code == "DENIED_HITL")' "$LOG"
    ;;

  retries)
    echo "── High Pydantic Retry Count (≥ 2) ─────"
    jq 'select(.pydantic_retry_count >= 2)' "$LOG"
    ;;

  policy-fails)
    echo "── Policy Check Failures ───────────────"
    jq 'select(.policy_checks_failed | length > 0) | {decision_code, ticker, policy_checks_failed}' "$LOG"
    ;;

  timeline)
    echo "── Decision Timeline ───────────────────"
    jq -r '[._written_at, .decision_code, (.ticker // "N/A"), ("$" + (.estimated_value_usd | tostring))] | @tsv' "$LOG"
    ;;

  *)
    echo "Usage: bash observability/query_audit.sh [command]"
    echo ""
    echo "Commands:"
    echo "  summary         Overview of all decisions (default)"
    echo "  rejections      All REJECTED_* entries"
    echo "  consensus-misses  Where agents disagreed"
    echo "  hitl            PENDING / APPROVED / DENIED_HITL"
    echo "  retries         High Pydantic retry count entries"
    echo "  policy-fails    Entries with policy check failures"
    echo "  timeline        Chronological decision timeline"
    ;;
esac
