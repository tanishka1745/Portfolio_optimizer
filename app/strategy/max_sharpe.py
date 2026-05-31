import numpy as np
from scipy.optimize import minimize

def portfolio_return_and_vol(weights, securities):
    """
    Computes the mean return and standard deviation (volatility) of the portfolio
    constructed from the given weights and security return series.
    """
    returns = np.array([s.returns for s in securities])
    port_returns = np.dot(weights, returns)
    mean = float(np.mean(port_returns))
    vol = float(np.std(port_returns, ddof=0))
    return mean, vol

def negative_sharpe(weights, securities, risk_free=0.0):
    """
    Objective function for Sharpe Ratio maximization.
    Since minimize functions find local minima, we minimize the negative Sharpe Ratio:
    Sharpe = (mean_return - risk_free) / volatility
    """
    mean, vol = portfolio_return_and_vol(weights, securities)
    if vol == 0:
        return 1e6
    sharpe = (mean - risk_free) / vol
    return -sharpe

def max_sharpe_strategy(request, bounds, extra_constraints=None):
    """
    Maximizes the portfolio Sharpe Ratio subject to budget, security bounds,
    and optional portfolio-level constraints (like dividend yield).
    """
    securities = request.securities
    n = len(securities)

    initial = np.array([1 / n] * n)
    
    # Capital allocation budget constraint
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    if extra_constraints:
        if isinstance(extra_constraints, list):
            constraints.extend(extra_constraints)
        else:
            constraints.append(extra_constraints)

    result = minimize(
        negative_sharpe,
        initial,
        args=(securities,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    # Throw descriptive validation error if constraints are incompatible/infeasible
    if not result.success:
        raise ValueError(f"Maximize Sharpe optimization failed: {result.message}")

    return result.x
