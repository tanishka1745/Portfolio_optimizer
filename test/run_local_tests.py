from app.models.request_model import OptimizationRequest, Security, Constraints
from app.services.optimizer_service import optimize_portfolio
import pandas as pd
import numpy as np
import os
import json


def read_examples(sec_path, factor_path=None):
    df = pd.read_excel(sec_path)
    # identify return columns
    required = {'ticker', 'security_name', 'current_weight'}
    return_cols = [c for c in df.columns if c not in required and c != 'dividend_yield']

    secs = []
    for _, row in df.iterrows():
        sec = Security(
            ticker=str(row['ticker']),
            security_name=str(row['security_name']),
            current_weight=float(row['current_weight']),
            returns=[float(row[c]) for c in return_cols],
            dividend_yield=float(row['dividend_yield']) if 'dividend_yield' in df.columns and not pd.isna(row['dividend_yield']) else None
        )
        secs.append(sec)

    factors = None
    if factor_path:
        fdf = pd.read_excel(factor_path)
        factor_cols = [c for c in fdf.columns if c.lower() != 'date']
        factors = {c: list(fdf[c].astype(float).values) for c in factor_cols}

    return secs, factors


def cagr(returns):
    # assumes periodic returns (e.g., monthly), returns in decimals
    cum = np.prod(1 + np.array(returns))
    periods = len(returns)
    # annualize assuming monthly
    years = periods / 12.0
    if years == 0:
        return 0.0
    return cum ** (1 / years) - 1


def vol(returns):
    return float(np.std(returns, ddof=0) * np.sqrt(12))  # annualized


def max_drawdown(returns):
    cum = np.cumprod(1 + np.array(returns))
    peak = np.maximum.accumulate(cum)
    drawdown = (cum - peak) / peak
    return float(np.min(drawdown))


if __name__ == '__main__':
    # If a sample JSON request exists, run it first for quick validation
    sample_path = 'test/example_inputs/sample_request.json'
    if os.path.exists(sample_path):
        with open(sample_path, 'r') as f:
            payload = json.load(f)

        # build securities
        secs = []
        for s in payload.get('securities', []):
            sec = Security(
                ticker=s['ticker'],
                security_name=s.get('security_name', ''),
                current_weight=float(s.get('current_weight', 0)),
                returns=[float(x) for x in s.get('returns', [])]
            )
            secs.append(sec)

        req = OptimizationRequest(
            strategy=payload.get('strategy', 'equal_weight'),
            securities=secs,
            constraints=Constraints(**payload.get('constraints', {}))
        )

        print('Running sample_request.json')
        out = optimize_portfolio(req)
        print(out)

    else:
        print('No sample JSON found at', sample_path)

    sec_path = 'test/example_inputs/securities.xlsx'
    factor_path = 'test/example_inputs/factors.xlsx'

    secs, factors = read_examples(sec_path, factor_path)

    req = OptimizationRequest(
        strategy='equal_weight',
        securities=secs,
        constraints=Constraints(),
        factor_returns=factors
    )

    print('Running Equal Weight')
    out = optimize_portfolio(req)
    print(out)

    req.strategy = 'risk_parity'
    print('\nRunning Risk Parity')
    out = optimize_portfolio(req)
    print(out)

    req.strategy = 'minimize_volatility'
    print('\nRunning Minimize Volatility')
    out = optimize_portfolio(req)
    print(out)

    req.strategy = 'minimize_drawdown'
    print('\nRunning Minimize Drawdown')
    out = optimize_portfolio(req)
    print(out)

    req.strategy = 'max_sharpe'
    print('\nRunning Max Sharpe')
    out = optimize_portfolio(req)
    print(out)

    # factor exposure optimization example: maximize Momentum
    req.strategy = 'optimize_factor_exposure'
    # set factor_targets in constraints
    req.constraints.factor_targets = {'Momentum': 'max', 'Value': 'min', 'Size': 'min'}
    print('\nRunning Optimize Factor Exposure (Momentum max)')
    out = optimize_portfolio(req)
    print(out)

    # compute portfolio metrics for optimized weights of last run
    allocs = out['allocation_changes']
    weights = np.array([a['optimized_weight'] for a in allocs]) / 100.0
    # compute portfolio returns series
    returns_matrix = np.array([s.returns for s in secs])
    port_returns = np.dot(weights, returns_matrix)
    print('\nOptimized portfolio CAGR:', cagr(port_returns))
    print('Optimized portfolio Annualized Vol:', vol(port_returns))
    print('Optimized portfolio Max Drawdown:', max_drawdown(port_returns))
