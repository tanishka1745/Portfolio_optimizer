from app.models.request_model import OptimizationRequest, Security, Constraints
from app.services.optimizer_service import optimize_portfolio
import json

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

if __name__ == '__main__':
    print("==============================================================")
    print("RUNNING PORTFOLIO OPTIMIZER VALIDATION FOR TEST CASES 1 TO 6")
    print("==============================================================\n")

    # Scenario 1: Basic equal-weight sanity check
    # Input: IEFA: 25%, SPY: 75%
    # Strategy: Equal Weights
    # Constraints: None
    req1 = build_request("equal_weight", {"IEFA": 25.0, "SPY": 75.0})
    res1 = optimize_portfolio(req1)
    print("--- SCENARIO 1: Basic Equal-Weight Sanity Check ---")
    print(json.dumps(res1, indent=2))
    print("\n" + "="*60 + "\n")

    # Scenario 2: Risk-based allocation across different asset classes
    # Input: VEA: 25%, AGG: 75%
    # Strategy: Risk Parity
    # Constraints: None
    req2 = build_request("risk_parity", {"VEA": 25.0, "AGG": 75.0})
    res2 = optimize_portfolio(req2)
    print("--- SCENARIO 2: Risk Parity ---")
    print(json.dumps(res2, indent=2))
    print("\n" + "="*60 + "\n")

    # Scenario 3: Lowest-risk portfolio construction
    # Input: SPY: 60%, AGG: 30%, GLD: 10%
    # Strategy: Minimize Volatility
    # Constraints: None
    req3 = build_request("minimize_volatility", {"SPY": 60.0, "AGG": 30.0, "GLD": 10.0})
    res3 = optimize_portfolio(req3)
    print("--- SCENARIO 3: Minimize Volatility ---")
    print(json.dumps(res3, indent=2))
    print("\n" + "="*60 + "\n")

    # Scenario 4: Risk-adjusted return optimization
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Maximize Sharpe Ratio
    # Constraints: None
    req4 = build_request("max_sharpe", {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0})
    res4 = optimize_portfolio(req4)
    print("--- SCENARIO 4: Maximize Sharpe Ratio ---")
    print(json.dumps(res4, indent=2))
    print("\n" + "="*60 + "\n")

    # Scenario 5: Portfolio-level and security-level constraint handling
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Maximize Sharpe Ratio
    # Constraints: Min Dividend Yield: 2.50%; each security min: 5%, max: 40%
    req5 = build_request(
        "max_sharpe", 
        {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0},
        min_w=0.05,
        max_w=0.40,
        min_yield=0.025
    )
    res5 = optimize_portfolio(req5)
    print("--- SCENARIO 5: Maximize Sharpe with Constraints ---")
    print(json.dumps(res5, indent=2))
    print("\n" + "="*60 + "\n")

    # Scenario 6: Momentum factor exposure
    # Input: IEFA: 20%, GLD: 20%, AGG: 20%, VEA: 20%, SPY: 20%
    # Strategy: Optimize Factor Exposure
    # Constraints: Maximize Momentum
    req6 = build_request(
        "optimize_factor_exposure",
        {"IEFA": 20.0, "GLD": 20.0, "AGG": 20.0, "VEA": 20.0, "SPY": 20.0},
        factor_targets={"Momentum": "max"}
    )
    res6 = optimize_portfolio(req6)
    print("--- SCENARIO 6: Momentum Factor Exposure ---")
    print(json.dumps(res6, indent=2))
    print("==============================================================")
