import numpy as np
from scipy.optimize import minimize

from app.utils.covariance import get_covariance_matrix


def portfolio_volatility(weights, cov_matrix):
    return np.sqrt(
        np.dot(weights.T, np.dot(cov_matrix, weights))
    )


def risk_parity_objective(weights, cov_matrix):
    cov = cov_matrix
    port_vol = portfolio_volatility(weights, cov)
    marginal = np.dot(cov, weights)
    contrib = weights * marginal
    target = port_vol / len(weights)
    return np.sum((contrib - target) ** 2)


def risk_parity_strategy(request):
    securities = request.securities
    n = len(securities)

    cov_matrix = get_covariance_matrix(securities)

    initial_weights = np.array([1 / n] * n)

    bounds = [(0, 1)] * n

    constraints = {
        'type': 'eq',
        'fun': lambda w: np.sum(w) - 1
    }

    result = minimize(
        risk_parity_objective,
        initial_weights,
        args=(cov_matrix,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    return result.x
