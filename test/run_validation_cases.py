from app.models.request_model import OptimizationRequest, Security, Constraints
from app.services.optimizer_service import optimize_portfolio
import json
import os
from typing import Dict, Any

def build_request(strategy, securities_list, min_w=None, max_w=None, min_yield=None, factor_targets=None):
    securities = []
    for ticker, weight in securities_list.items():
        securities.append(Security(
            ticker=ticker,
            security_name="", # Will be populated from Data.xlsx
            current_weight=weight,
            returns=None, # Will be populated from Data.xlsx
            dividend_yield=None # Will be populated from Data.xlsx
        ))
    
    constraints = None
    if min_w is not None or max_w is not None or min_yield is not None or factor_targets is not None:
        constraints = Constraints(
            min_weight=min_w,
            max_weight=max_w,
            min_dividend_yield=min_yield,
            factor_targets=factor_targets
        )
        
    return OptimizationRequest(
        strategy=strategy,
        securities=securities,
        constraints=constraints
    )

def save_responses(responses: Dict[str, Any], filename: str = "validation_responses.json"):
    """Save responses to JSON file for validation."""
    filepath = filename
    with open(filepath, 'w') as f:
        json.dump(responses, f, indent=2)
    print(f"\n✓ Responses saved to {filepath}")
    return filepath

if __name__ == '__main__':
    print("="*80)
    print("PORTFOLIO OPTIMIZER - 6 VALIDATION TEST CASES")
    print("="*80 + "\n")
    
    responses = {}

    # Scenario 1: Basic equal-weight sanity check
    # Input: IEFA: 25%, SPY: 75%
    # Strategy: Equal Weights
    # Constraints: None
    print("[1/6] Running: Basic Equal-Weight Sanity Check...")
    req1 = build_request("equal_weight", {"IEFA": 25.0, "SPY": 75.0})
    res1 = optimize_portfolio(req1)
    responses['case_1'] = res1
    print("✓ Case 1 complete\n")

    # Scenario 2: Risk-based allocation across different asset classes
    # Input: VEA: 25%, AGG: 75%
    # Strategy: Risk Parity
    # Constraints: None
    print("[2/6] Running: Risk-Based Allocation (Risk Parity)...")
    req2 = build_request("risk_parity", {"VEA": 25.0, "AGG": 75.0})
    res2 = optimize_portfolio(req2)
    responses['case_2'] = res2
    print("✓ Case 2 complete\n")

    # Scenario 3: Lowest-risk portfolio construction
    # Input: SPY: 60%, AGG: 30%, GLD: 10%
    # Strategy: Minimize Volatility
    # Constraints: None
    print("[3/6] Running: Lowest-Risk Portfolio (Minimize Volatility)...")
    req3 = build_request("minimize_volatility", {"SPY": 60.0, "AGG": 30.0, "GLD": 10.0})
    res3 = optimize_portfolio(req3)
    responses['case_3'] = res3
    print("✓ Case 3 complete\n")

    # Scenario 4: Risk-adjusted return optimization
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Maximize Sharpe Ratio
    # Constraints: None
    print("[4/6] Running: Risk-Adjusted Return Optimization (Maximize Sharpe)...")
    req4 = build_request("max_sharpe", {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0})
    res4 = optimize_portfolio(req4)
    responses['case_4'] = res4
    print("✓ Case 4 complete\n")

    # Scenario 5: Portfolio-level and security-level constraint handling
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Maximize Sharpe Ratio
    # Constraints: Min Dividend Yield: 2.50%; each security min: 5%, max: 40%
    print("[5/6] Running: Constraint Handling (Maximize Sharpe with Constraints)...")
    req5 = build_request(
        "max_sharpe", 
        {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0},
        min_w=0.05,
        max_w=0.40,
        min_yield=0.025
    )
    res5 = optimize_portfolio(req5)
    responses['case_5'] = res5
    print("✓ Case 5 complete\n")

    # Scenario 6: Momentum factor exposure
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Optimize Factor Exposure
    # Constraints: Maximize Momentum
    print("[6/6] Running: Momentum Factor Exposure (Bonus)...")
    req6 = build_request(
        "optimize_factor_exposure",
        {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0},
        factor_targets={"Momentum": "max"}
    )
    res6 = optimize_portfolio(req6)
    responses['case_6'] = res6
    print("✓ Case 6 complete\n")

    # Save all responses to JSON
    print("="*80)
    save_responses(responses)
    
    # Print summary
    print("\n" + "="*80)
    print("VALIDATION RESULTS SUMMARY")
    print("="*80)
    for i in range(1, 7):
        case_key = f'case_{i}'
        if case_key in responses:
            print(f"✓ Case {i}: Response received")
    
    print("\n" + "="*80)
    print("Next: Run validation checker with:")
    print("  python test/validate_acceptance_criteria.py")
    print("="*80)
