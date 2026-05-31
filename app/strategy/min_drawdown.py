import numpy as np
from scipy.optimize import minimize

from app.utils.covariance import get_covariance_matrix


def portfolio_returns_series(weights, securities):
    returns = np.array([s.returns for s in securities])
    # returns shape: (n_securities, t)
    port_returns = np.dot(weights, returns)
    return port_returns


def max_drawdown(returns_series):
    cum = np.cumprod(1 + returns_series)  # cumulative growth
    peak = np.maximum.accumulate(cum)
    drawdown = (cum - peak) / peak
    return float(np.min(drawdown))  # negative value


def min_drawdown_objective(weights, securities):
    port_returns = portfolio_returns_series(weights, securities)
    return max_drawdown(port_returns)


def minimize_drawdown_strategy(request, bounds):
    securities = request.securities
    n = len(securities)

    initial = np.array([1 / n] * n)

    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)

    result = minimize(
        min_drawdown_objective,
        initial,
        args=(securities,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    if not result.success:
        raise ValueError(f"Minimize drawdown optimization failed: {result.message}")

    return result.x

