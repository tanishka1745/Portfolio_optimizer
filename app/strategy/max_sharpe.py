import numpy as np
from scipy.optimize import minimize


def portfolio_return_and_vol(weights, securities):
    returns = np.array([s.returns for s in securities])
    port_returns = np.dot(weights, returns)
    mean = float(np.mean(port_returns))
    vol = float(np.std(port_returns, ddof=0))
    return mean, vol


def negative_sharpe(weights, securities, risk_free=0.0):
    mean, vol = portfolio_return_and_vol(weights, securities)
    if vol == 0:
        return 1e6
    sharpe = (mean - risk_free) / vol
    return -sharpe


def max_sharpe_strategy(request):
    securities = request.securities
    n = len(securities)

    initial = np.array([1 / n] * n)
    bounds = [(0, 1)] * n
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)

    result = minimize(
        negative_sharpe,
        initial,
        args=(securities,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    return result.x
