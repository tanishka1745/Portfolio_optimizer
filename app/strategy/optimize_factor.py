import numpy as np
from scipy.optimize import minimize


def portfolio_returns_series(weights, securities):
    returns = np.array([s.returns for s in securities])
    port_returns = np.dot(weights, returns)
    return port_returns


def regress_betas(port_returns, factor_matrix):
    # factor_matrix: (t, k)
    X = np.column_stack([np.ones(len(port_returns)), factor_matrix])
    y = port_returns
    betas, *_ = np.linalg.lstsq(X, y, rcond=None)
    # return only factor betas (exclude intercept)
    return betas[1:]


def factor_objective(weights, securities, factors, factor_targets):
    # factors: dict name->array (t,)
    port = portfolio_returns_series(weights, securities)
    # build factor matrix in provided factor_targets order
    names = list(factor_targets.keys())
    factor_matrix = np.column_stack([factors[name] for name in names])
    betas = regress_betas(port, factor_matrix)
    # objective: sum over factors of -beta if maximize, +beta if minimize
    obj = 0.0
    for i, name in enumerate(names):
        direction = factor_targets[name].lower()
        if direction == 'maximize' or direction == 'max':
            obj -= betas[i]
        else:
            obj += betas[i]
    return obj


def optimize_factor_exposure_strategy(request):
    securities = request.securities
    n = len(securities)

    if not request.factor_returns or not request.constraints or not request.constraints.factor_targets:
        raise Exception('Factor returns and factor_targets constraint required for this strategy')

    factors = request.factor_returns
    factor_targets = request.constraints.factor_targets

    # ensure factors lengths match securities returns length
    initial = np.array([1 / n] * n)
    bounds = [(0, 1)] * n
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)

    result = minimize(
        factor_objective,
        initial,
        args=(securities, factors, factor_targets),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    return result.x
