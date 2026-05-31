import numpy as np
from scipy.optimize import minimize

def portfolio_returns_series(weights, securities):
    """
    Calculates the combined historical daily return series of the portfolio.
    """
    returns = np.array([s.returns for s in securities])
    port_returns = np.dot(weights, returns)
    return port_returns

def regress_betas(port_returns, factor_matrix):
    """
    Performs multiple linear regression (OLS) to estimate the factor betas (ex intercept)
    for the portfolio return series against a set of factor return series.
    """
    # Create feature matrix with constant intercept column
    X = np.column_stack([np.ones(len(port_returns)), factor_matrix])
    y = port_returns
    # Least squares solver
    betas, *_ = np.linalg.lstsq(X, y, rcond=None)
    # Exclude intercept coefficient (betas[0]) and return factor betas
    return betas[1:]

def factor_objective(weights, securities, factors, factor_targets):
    """
    Objective function for factor exposure optimization.
    Calculates portfolio returns, runs factor regression, and compiles the objective:
    - Minimizes -beta (equivalent to maximizing beta) for factors targeted as 'max'.
    - Minimizes +beta (equivalent to minimizing beta) for factors targeted as 'min'.
    """
    port = portfolio_returns_series(weights, securities)
    # Assemble factor columns in the order defined by factor_targets keys
    names = list(factor_targets.keys())
    factor_columns = []
    for name in names:
        matched_key = None
        for k in factors.keys():
            if k.lower() == name.lower():
                matched_key = k
                break
        if matched_key is None:
            raise ValueError(f"Factor '{name}' not found in factor returns. Available factors: {list(factors.keys())}")
        factor_columns.append(factors[matched_key])
        
    factor_matrix = np.column_stack(factor_columns)
    betas = regress_betas(port, factor_matrix)
    
    obj = 0.0
    for i, name in enumerate(names):
        direction = factor_targets[name].lower()
        if direction == 'maximize' or direction == 'max':
            obj -= betas[i]  # Maximizing loading
        else:
            obj += betas[i]  # Minimizing loading
    return obj

def optimize_factor_exposure_strategy(request, bounds):
    """
    Finds optimal weights that maximize or minimize exposures to Fama-French/other factors
    subject to budget limits and security-level weight bounds.
    """
    securities = request.securities
    n = len(securities)

    if not request.factor_returns or not request.constraints or not request.constraints.factor_targets:
        raise Exception('Factor returns and factor_targets constraint required for this strategy')

    factors = request.factor_returns
    factor_targets = request.constraints.factor_targets

    initial = np.array([1 / n] * n)
    
    # Capital allocation constraint
    constraints = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1},)

    result = minimize(
        factor_objective,
        initial,
        args=(securities, factors, factor_targets),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    # Check convergence; fail cleanly if constraints are infeasible
    if not result.success:
        raise ValueError(f"Optimize factor exposure optimization failed: {result.message}")

    return result.x
