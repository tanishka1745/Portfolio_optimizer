from app.strategy.equal_weight import equal_weight_strategy
from app.strategy.min_volatility import min_volatility_strategy
from app.strategy.risk_parity import risk_parity_strategy
from app.strategy.min_drawdown import minimize_drawdown_strategy
from app.strategy.max_sharpe import max_sharpe_strategy
from app.strategy.optimize_factor import optimize_factor_exposure_strategy
import numpy as np

from app.strategy.min_volatility import portfolio_volatility

def _apply_weight_bounds(request, n):
    # returns bounds per-security using constraints if provided
    if request.constraints:
        min_w = request.constraints.min_weight if request.constraints.min_weight is not None else 0
        max_w = request.constraints.max_weight if request.constraints.max_weight is not None else 1
    else:
        min_w, max_w = 0, 1
    return [(min_w, max_w)] * n

def _portfolio_returns(weights, securities):
    returns = np.array([s.returns for s in securities])
    return np.dot(weights, returns)

def _compute_factor_betas(port_returns, factors):
    # factors: dict name->list
    names = list(factors.keys())
    factor_matrix = np.column_stack([factors[n] for n in names])
    X = np.column_stack([np.ones(len(port_returns)), factor_matrix])
    betas, *_ = np.linalg.lstsq(X, port_returns, rcond=None)
    return {names[i]: float(betas[i+1]) for i in range(len(names))}

def optimize_portfolio(request):

    strategy = request.strategy

    n = len(request.securities)

    if strategy == "equal_weight":
        weights = equal_weight_strategy(request)

    elif strategy == "minimize_volatility":
        weights = min_volatility_strategy(request)

    elif strategy == "risk_parity":
        weights = risk_parity_strategy(request)

    elif strategy == "minimize_drawdown":
        weights = minimize_drawdown_strategy(request)

    elif strategy == "max_sharpe":
        weights = max_sharpe_strategy(request)

    elif strategy == "optimize_factor_exposure":
        weights = optimize_factor_exposure_strategy(request)

    else:
        raise Exception("Invalid strategy")

    response = []

    for i, security in enumerate(request.securities):
        optimized_weight = round(weights[i] * 100, 2)

        response.append({
            "ticker": security.ticker,
            "security_name": security.security_name,
            "current_weight": security.current_weight,
            "optimized_weight": optimized_weight,
            "change": round(optimized_weight - security.current_weight, 2)
        })

    result = {
        "optimization_strategy": strategy,
        "allocation_changes": response
    }

    # Bonus: compute factor betas if factor returns provided
    if request.factor_returns:
        # current portfolio
        current_weights = np.array([s.current_weight / 100.0 for s in request.securities])
        curr_port = _portfolio_returns(current_weights, request.securities)
        curr_betas = _compute_factor_betas(curr_port, request.factor_returns)

        # optimized portfolio
        opt_weights = np.array(weights)
        opt_port = _portfolio_returns(opt_weights, request.securities)
        opt_betas = _compute_factor_betas(opt_port, request.factor_returns)

        result["factor_betas"] = {
            "current_portfolio": curr_betas,
            "optimized_portfolio": opt_betas
        }

    return result