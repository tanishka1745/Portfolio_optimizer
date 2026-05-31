import numpy as np
from scipy.optimize import minimize

from app.utils.covariance import get_covariance_matrix

def portfolio_volatility(weights, cov_matrix):
    """
    Calculates the portfolio standard deviation (volatility) from weights and covariance.
    Formula: sqrt(w^T * Sigma * w)
    """
    return np.sqrt(
        np.dot(weights.T,
               np.dot(cov_matrix, weights))
    )

def min_volatility_strategy(request, bounds, extra_constraints=None):
    """
    Constructs the global minimum variance (minimum volatility) portfolio.
    Fits weights to minimize standard deviation subject to budget and bounds constraints.
    """
    securities = request.securities
    n = len(securities)

    # Estimate covariance matrix from asset daily returns
    cov_matrix = get_covariance_matrix(securities)

    initial_weights = np.array([1 / n] * n)

    # Capital allocation constraint: weights must sum to 1.0
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    if extra_constraints:
        if isinstance(extra_constraints, list):
            constraints.extend(extra_constraints)
        else:
            constraints.append(extra_constraints)

    result = minimize(
        portfolio_volatility,
        initial_weights,
        args=(cov_matrix,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    # Check for convergence; fail cleanly if constraints are infeasible
    if not result.success:
        raise ValueError(f"Minimize volatility optimization failed: {result.message}")

    return result.x
