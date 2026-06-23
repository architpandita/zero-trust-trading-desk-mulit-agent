import sys
import os
import time
from policy_server import PolicyServer, TradeProposal
from mock_broker import MockBroker
from agents import TechnicalAgent, FundamentalAgent, ExecutionAgent, ContextHygiene

# Terminal colors for premium visual aesthetics
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(title: str):
    print(f"\n{BLUE}{BOLD}" + "="*70)
    print(f" {title.center(68)}")
    print("="*70 + f"{RESET}\n")

def print_status(label: str, status: str, color=CYAN):
    print(f"{BOLD}{label:<25}:{RESET} {color}{status}{RESET}")

def main():
    print_header("ZERO-TRUST TRADING DESK HARNESS DEMO")
    
    # 1. Initialize Components
    config_path = "policy_config.yaml"
    if not os.path.exists(config_path):
        print(f"{RED}[ERROR]{RESET} Configuration file '{config_path}' not found. Please create it first.")
        sys.exit(1)

    print(f"{GREEN}[INIT]{RESET} Initializing Policy Server gateway...")
    server = PolicyServer(config_path)
    
    print(f"{GREEN}[INIT]{RESET} Initializing Mock Broker API...")
    broker = MockBroker(initial_cash=10000.00, log_file="broker_ledger.json")
    
    # Create agents
    tech_agent = TechnicalAgent()
    fund_agent = FundamentalAgent()
    exec_agent = ExecutionAgent()

    # 2. Context Hygiene Demonstration
    print_header("1. CONTEXT HYGIENE INTERCEPTION DEMO")
    raw_prompt_context = (
        "Agent execution environment loaded.\n"
        "MOCK_BROKER_API_KEY_SECRET = 'sk-prod-9a28e3b7c89f21d3e4f5a6b7'\n"
        "account_balance = 10000.00\n"
        "Executing analysis on stock AAPL. Retrieve moving averages."
    )
    print(f"{BOLD}Raw Context Stream (Contains secrets):{RESET}")
    print("-" * 50)
    print(raw_prompt_context)
    print("-" * 50)
    
    print(f"\n{YELLOW}[MIDDLEWARE]{RESET} Intercepting and sanitizing prompt payload...")
    sanitized_context = ContextHygiene.sanitize_context(raw_prompt_context)
    
    print(f"\n{GREEN}[SAFE]{RESET} Sanitized Context Stream (Sent to LLM Agent):")
    print("-" * 50)
    print(sanitized_context)
    print("-" * 50)
    time.sleep(1)

    # Setup mock market data for trading scenarios
    # Mock stock prices
    current_prices = {
        "QQQ": 400.00,
        "AAPL": 180.00,
        "DOGE": 0.15,
        "GME": 25.00
    }

    # ==============================================================================
    # SCENARIO A: Safe Trade - Automatic Execution
    # ==============================================================================
    print_header("2. SCENARIO A: Safe Trade (Automatic Execution)")
    ticker_a = "QQQ"
    qty_a = 2
    price_a = current_prices[ticker_a]
    
    print(f"{CYAN}[SWARM]{RESET} Orchestrating deliberation on {ticker_a}...")
    # Simulate agent analyzes
    tech_res = tech_agent.analyze(ticker_a, [390.0, 392.0, 395.0, 398.0, 400.0])
    fund_res = fund_agent.analyze(ticker_a, {"pe_ratio": 22, "revenue_growth": 0.12, "news_sentiment": "bullish"})
    
    proposal_dict, vibe_diff = exec_agent.generate_proposal(
        ticker=ticker_a,
        tech_rec=tech_res,
        fund_rec=fund_res,
        quantity=qty_a,
        price=price_a,
        first_trade_of_day=False
    )
    
    print(vibe_diff)
    print(f"\n{YELLOW}[GATE]{RESET} Submitting proposed JSON structure to Policy Server...")
    proposal_a = TradeProposal(**proposal_dict)
    
    decision, reasons = server.validate_proposal(proposal_a, current_portfolio_exposure=0.0)
    print_status("Policy Server Decision", decision, GREEN if decision == "ALLOW" else RED)
    
    if decision == "ALLOW":
        print(f"{GREEN}[EXECUTE]{RESET} Decision is ALLOW. Dispatching order to Broker...")
        success, msg = broker.execute_trade(ticker_a, proposal_a.action, proposal_a.quantity, proposal_a.price)
        print(f"Broker Response: {GREEN if success else RED}{msg}{RESET}")
    else:
        print(f"{RED}[BLOCKED]{RESET} Policy server rejected the trade: {reasons}")
    
    time.sleep(1)

    # ==============================================================================
    # SCENARIO B: Large Trade - Human-in-the-Loop Intercept
    # ==============================================================================
    print_header("3. SCENARIO B: Large Trade (HITL Intercept Required)")
    ticker_b = "AAPL"
    qty_b = 10
    price_b = current_prices[ticker_b]
    
    print(f"{CYAN}[SWARM]{RESET} Orchestrating deliberation on {ticker_b}...")
    tech_res_b = tech_agent.analyze(ticker_b, [170.0, 172.0, 175.0, 178.0, 180.0])
    fund_res_b = fund_agent.analyze(ticker_b, {"pe_ratio": 22, "revenue_growth": 0.08, "news_sentiment": "bullish"})
    
    proposal_dict_b, vibe_diff_b = exec_agent.generate_proposal(
        ticker=ticker_b,
        tech_rec=tech_res_b,
        fund_rec=fund_res_b,
        quantity=qty_b,
        price=price_b,
        first_trade_of_day=True
    )
    
    print(vibe_diff_b)
    print(f"\n{YELLOW}[GATE]{RESET} Submitting proposed JSON structure to Policy Server...")
    proposal_b = TradeProposal(**proposal_dict_b)
    
    current_exposure = broker.get_portfolio_exposure(current_prices)
    decision_b, reasons_b = server.validate_proposal(proposal_b, current_portfolio_exposure=current_exposure)
    print_status("Policy Server Decision", decision_b, YELLOW if decision_b == "HITL" else RED)
    
    if decision_b == "HITL":
        print(f"\n{YELLOW}{BOLD}[WARNING] HUMAN-IN-THE-LOOP AUTHORIZATION REQUIRED [WARNING]{RESET}")
        print(f"Triggers tripped:")
        for r in reasons_b:
            print(f" - {r}")
        
        # Interactive Prompt
        user_input = input(f"\nDo you approve the execution of this trade? (Y/N): ").strip().upper()
        if user_input == "Y":
            print(f"{GREEN}[APPROVED]{RESET} User approved trade. Sending to broker...")
            success, msg = broker.execute_trade(ticker_b, proposal_b.action, proposal_b.quantity, proposal_b.price)
            print(f"Broker Response: {GREEN if success else RED}{msg}{RESET}")
        else:
            print(f"{RED}[DENIED]{RESET} Human cancelled trade execution. Refusing broker call.")
    else:
        print(f"{RED}[BLOCKED]{RESET} Policy server rejected the trade: {reasons_b}")
        
    time.sleep(1)

    # ==============================================================================
    # SCENARIO C: Rogue Trade - Restricted Asset Class Intercept
    # ==============================================================================
    print_header("4. SCENARIO C: Rogue Trade (Hard Policy Block)")
    ticker_c = "DOGE"
    qty_c = 5000
    price_c = current_prices[ticker_c]
    
    print(f"{CYAN}[SWARM]{RESET} Compromised agent attempting unauthorized asset trade on {ticker_c}...")
    
    # Execution agent bypasses standard analysis consensus (rogue execution attempt)
    rogue_proposal = TradeProposal(
        ticker=ticker_c,
        action="BUY",
        quantity=qty_c,
        price=price_c,
        agent_role="execution_agent",
        asset_class="CRYPTO"
    )
    
    print(f"\n{YELLOW}[GATE]{RESET} Submitting rogue proposed JSON to Policy Server...")
    current_exposure = broker.get_portfolio_exposure(current_prices)
    decision_c, reasons_c = server.validate_proposal(rogue_proposal, current_portfolio_exposure=current_exposure)
    
    print_status("Policy Server Decision", decision_c, RED)
    
    if decision_c == "DENY":
        print(f"{RED}[HARD BLOCK]{RESET} Trade request strictly BLOCKED by policy rules. Broker request aborted.")
        print(f"{BOLD}Violation details:{RESET}")
        for r in reasons_c:
            print(f" {RED}[!] {r}{RESET}")
    else:
        print(f"{GREEN}[EXECUTE]{RESET} Warning: Rogue trade slipped past server! Action: {decision_c}")
        
    print_header("DEMO SUMMARY")
    portfolio_val = broker.get_total_portfolio_value(current_prices)
    portfolio_exposure = broker.get_portfolio_exposure(current_prices)
    print_status("Remaining Broker Cash", f"${broker.cash:,.2f}", GREEN)
    print_status("Stock Positions Held", f"{broker.positions}", CYAN)
    print_status("Total Portfolio Exposure", f"${portfolio_exposure:,.2f}", CYAN)
    print_status("Total Portfolio Net Worth", f"${portfolio_val:,.2f}", GREEN)
    print(f"\n{GREEN}[DONE]{RESET} Verification demo executed successfully.\n")

if __name__ == "__main__":
    main()
