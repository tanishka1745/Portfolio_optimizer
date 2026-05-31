import numpy as np
from scipy.optimize import minimize

from app.utils.covariance import get_covariance_matrix

def portfolio_volatility(weights, cov_matrix):
    """
    Calculates the portfolio standard deviation (volatility).
    Formula: sqrt(w^T * Sigma * w)
    """
    return np.sqrt(
        np.dot(weights.T, np.dot(cov_matrix, weights))
    )

def risk_parity_objective(weights, cov_matrix):
    """
    Calculates the Risk Parity (Equal Risk Contribution) objective value.
    Uses the scale-independent Relative Risk Contribution (RRC) formulation:
    RRC_i = w_i * (Sigma * w)_i / (w^T * Sigma * w)
    Objective: Minimize the sum of squared differences between each asset's RRC and 1/N.
    """
    port_var = np.dot(weights.T, np.dot(cov_matrix, weights))
    if port_var == 0:
        return 1e6
    marginal = np.dot(cov_matrix, weights)
    contrib = weights * marginal
    rrc = contrib / port_var
    target = 1.0 / len(weights)
    return np.sum((rrc - target) ** 2)

def risk_parity_strategy(request, bounds):
    """
    Performs Risk Parity optimization under budget constraints (sum of weights = 1.0)
    and security bounds (no short selling).
    """
    securities = request.securities
    n = len(securities)

    # Estimate covariance matrix from daily return series
    cov_matrix = get_covariance_matrix(securities)

    # Start with equal capital weights
    initial_weights = np.array([1 / n] * n)

    # Budget constraint: weights must sum to 100%
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

    # Check for optimizer convergence
    if not result.success:
        raise ValueError(f"Risk parity optimization failed: {result.message}")

    return result.x
