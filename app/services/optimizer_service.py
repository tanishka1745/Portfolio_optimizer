from app.strategy.equal_weight import equal_weight_strategy
from app.strategy.min_volatility import min_volatility_strategy
from app.strategy.risk_parity import risk_parity_strategy
from app.strategy.min_drawdown import minimize_drawdown_strategy
from app.strategy.max_sharpe import max_sharpe_strategy
from app.strategy.optimize_factor import optimize_factor_exposure_strategy
import numpy as np
import os
import pandas as pd
import yfinance as yf
import urllib.request
import zipfile

from app.strategy.min_volatility import portfolio_volatility

def _apply_weight_bounds(request, n):
    """
    Constructs the security-level lower and upper weight bounds.
    Converts constraints from percentages to decimals (e.g., 5% -> 0.05) if necessary.
    """
    if request.constraints:
        min_w = request.constraints.min_weight if request.constraints.min_weight is not None else 0
        max_w = request.constraints.max_weight if request.constraints.max_weight is not None else 1
    else:
        min_w, max_w = 0, 1
    
    # Handle percentage values gracefully (e.g., 5.0 -> 0.05, 40.0 -> 0.40)
    if min_w > 1.0:
        min_w = min_w / 100.0
    if max_w > 1.0:
        max_w = max_w / 100.0
        
    return [(min_w, max_w)] * n

def _portfolio_returns(weights, securities):
    """
    Calculates the combined historical return series of the portfolio.
    """
    returns = np.array([s.returns for s in securities])
    return np.dot(weights, returns)

def _compute_factor_betas(port_returns, factors):
    """
    Performs multiple linear regression (OLS) to estimate the factor betas (ex intercept)
    for a given portfolio return series against a set of factor return series.
    """
    names = list(factors.keys())
    factor_matrix = np.column_stack([factors[n] for n in names])
    # Add intercept column (constant) to the feature matrix
    X = np.column_stack([np.ones(len(port_returns)), factor_matrix])
    betas, *_ = np.linalg.lstsq(X, port_returns, rcond=None)
    # Exclude the intercept beta (betas[0]) and return factor loading dict
    return {names[i].lower(): float(betas[i+1]) for i in range(len(names))}

def _ensure_data_is_loaded(request):
    """
    Ensures that historical return series, asset names, dividend yields, and factor returns
    are fully populated. 
    1. Attempts to load from the local 'Data.xlsx' if asset returns are missing.
    2. Falls back to Yahoo Finance downloads for asset returns and yields.
    3. Falls back to Kenneth French Data Library for Fama-French Momentum daily factors if needed.
    """
    has_returns = all(s.returns is not None and len(s.returns) > 0 for s in request.securities)
    
    # 1. Try loading from the local workspace Data.xlsx
    if not has_returns and os.path.exists("Data.xlsx"):
        try:
            xls = pd.ExcelFile("Data.xlsx")
            df_info = pd.read_excel(xls, sheet_name='Fund Info')
            df_returns = pd.read_excel(xls, sheet_name='Fund Returns')
            
            # Map tickers to their metadata (names and yield)
            info_dict = {}
            for _, row in df_info.iterrows():
                info_dict[row['ticker']] = {
                    'name': row['fund_name'],
                    'yield': float(row['dividend_yield']) if not pd.isna(row['dividend_yield']) else 0.0
                }
            
            # Pivot the long format return data to date-indexed wide format
            p_returns = df_returns.pivot(index='date', columns='ticker', values='total_return').dropna()
            
            common_idx = p_returns.index
            p_factors = None
            # Check for factor returns in Excel sheet
            if 'Factor Returns' in xls.sheet_names:
                df_factors = pd.read_excel(xls, sheet_name='Factor Returns')
                p_factors = df_factors.pivot(index='date', columns='index_ticker', values='total_return').dropna()
                p_factors = p_factors.rename(columns={
                    'Momentum Factor': 'Momentum',
                    'Value Factor': 'Value',
                    'Size Factor': 'Size'
                })
                # Align overlapping dates across assets and factors
                common_idx = common_idx.intersection(p_factors.index)
            
            for security in request.securities:
                ticker = security.ticker
                if ticker in p_returns.columns:
                    security.returns = list(p_returns.loc[common_idx, ticker].values)
                
                # Fetch metadata from info sheet
                if ticker in info_dict:
                    if not security.security_name:
                        security.security_name = info_dict[ticker]['name']
                    if security.dividend_yield is None:
                        dy = info_dict[ticker]['yield']
                        if dy > 1.0:
                            dy = dy / 100.0  # Normalize percentage to decimal
                        security.dividend_yield = dy
                else:
                    if security.dividend_yield is None:
                        security.dividend_yield = 0.0
            
            # Populate factor returns if present
            if p_factors is not None and not request.factor_returns:
                request.factor_returns = {}
                for col in p_factors.columns:
                    request.factor_returns[col] = list(p_factors.loc[common_idx, col].values)
            
            # Save calendar years
            dates = pd.to_datetime(common_idx)
            request.years = float((dates[-1] - dates[0]).days / 365.25)
            
            has_returns = True
        except Exception:
            pass  # Fall back to Yahoo Finance if Excel reading encounters issues

    # 2. Fallback to Yahoo Finance for asset returns and yields
    if not has_returns:
        tickers = [s.ticker for s in request.securities]
        try:
            # Download price data starting from standard launch date threshold
            df_assets = yf.download(tickers, start="2012-10-22")['Close'].ffill().dropna()
            asset_returns = df_assets.pct_change().dropna()
            
            # Save calendar years
            dates = pd.to_datetime(asset_returns.index)
            request.years = float((dates[-1] - dates[0]).days / 365.25)
            
            for security in request.securities:
                ticker = security.ticker
                if ticker in asset_returns.columns:
                    security.returns = list(asset_returns[ticker].values)
                if security.dividend_yield is None:
                    try:
                        dy = yf.Ticker(ticker).info.get('dividendYield', 0.0)
                        if dy is None:
                            dy = 0.0
                        if dy > 1.0:
                            dy = dy / 100.0
                        security.dividend_yield = dy
                    except Exception:
                        security.dividend_yield = 0.0
        except Exception as exc:
            raise Exception(f"Failed to load historical returns: {exc}")

    # Ensure all security yields are normalized
    for s in request.securities:
        if s.dividend_yield is None:
            s.dividend_yield = 0.0
        elif s.dividend_yield > 1.0:
            s.dividend_yield = s.dividend_yield / 100.0

    # 3. Fallback to Kenneth French Data Library for Fama-French Momentum factor
    if (request.strategy == "optimize_factor_exposure" or request.factor_returns is None) and not request.factor_returns:
        try:
            urllib.request.urlretrieve('https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip', 'mom.zip')
            z_mom = zipfile.ZipFile('mom.zip')
            df_mom = pd.read_csv(z_mom.open('F-F_Momentum_Factor_daily.csv'), skiprows=13)
            df_mom.columns = ['Date', 'Mom']
            df_mom['Date'] = pd.to_numeric(df_mom['Date'], errors='coerce')
            df_mom = df_mom.dropna(subset=['Date'])
            df_mom['Date'] = df_mom['Date'].astype(int)
            df_mom['Date'] = pd.to_datetime(df_mom['Date'], format='%Y%m%d')
            df_mom.set_index('Date', inplace=True)
            df_mom['Mom'] = df_mom['Mom'].astype(float) / 100.0
            
            # Align lengths
            n_returns = len(request.securities[0].returns)
            df_mom_tail = df_mom.tail(n_returns)
            request.factor_returns = {
                'Momentum': list(df_mom_tail['Mom'].values)
            }
        except Exception as exc:
            raise Exception(f"Failed to load Fama-French factor returns: {exc}")

def optimize_portfolio(request):
    """
    Main entry point for portfolio optimization.
    Applies bounds, compiles constraints, executes strategies, and formats responses.
    """
    # Verify that returns and factor series are loaded and aligned
    _ensure_data_is_loaded(request)

    strategy = request.strategy
    n = len(request.securities)

    # Apply lower/upper bounds per security
    bounds = _apply_weight_bounds(request, n)

    # Compile portfolio-level constraints (e.g. Min Dividend Yield)
    extra_constraints = []
    if request.constraints and request.constraints.min_dividend_yield is not None:
        min_yield = request.constraints.min_dividend_yield
        if min_yield > 1.0:
            min_yield = min_yield / 100.0
        
        dy = np.array([s.dividend_yield for s in request.securities])
        # Inequality constraint format for SciPy: sum(w_i * dy_i) - min_yield >= 0
        extra_constraints.append({
            'type': 'ineq',
            'fun': lambda w, dy=dy, my=min_yield: np.dot(w, dy) - my
        })

    # Execute the requested optimization strategy
    if strategy == "equal_weight":
        weights = equal_weight_strategy(request)

    elif strategy == "minimize_volatility":
        weights = min_volatility_strategy(request, bounds, extra_constraints)

    elif strategy == "risk_parity":
        weights = risk_parity_strategy(request, bounds)

    elif strategy == "minimize_drawdown":
        weights = minimize_drawdown_strategy(request, bounds)

    elif strategy == "max_sharpe":
        weights = max_sharpe_strategy(request, bounds, extra_constraints)

    elif strategy == "optimize_factor_exposure":
        weights = optimize_factor_exposure_strategy(request, bounds)

    else:
        raise Exception("Invalid strategy")

    # Format the allocation changes response
    response = []
    for i, security in enumerate(request.securities):
        optimized_weight = round(weights[i] * 100, 2)
        response.append({
            "ticker": security.ticker,
            "security_name": security.security_name,
            "security name": security.security_name,
            "current_weight": security.current_weight,
            "optimized_weight": optimized_weight,
            "allocation": optimized_weight,
            "min_weight": round(bounds[i][0] * 100, 2),
            "min weight": round(bounds[i][0] * 100, 2),
            "max_weight": round(bounds[i][1] * 100, 2),
            "max weight": round(bounds[i][1] * 100, 2),
            "change": round(optimized_weight - security.current_weight, 2)
        })

    result = {
        "optimization_strategy": strategy,
        "allocation_changes": response
    }



    # Compute portfolio factor betas for current and optimized portfolios
    if request.factor_returns:
        current_weights = np.array([s.current_weight / 100.0 for s in request.securities])
        curr_port = _portfolio_returns(current_weights, request.securities)
        curr_betas = _compute_factor_betas(curr_port, request.factor_returns)

        opt_weights = np.array(weights)
        opt_port = _portfolio_returns(opt_weights, request.securities)
        opt_betas = _compute_factor_betas(opt_port, request.factor_returns)

        result["factor_betas"] = {
            "current_portfolio": curr_betas,
            "optimized_portfolio": opt_betas
        }

    return result

def _calculate_portfolio_metrics(weights, request):
    """
    Computes CAGR, Volatility, Sharpe Ratio, Cumulative Return, Expected Return,
    Max Drawdown, Dividend Yield, and Annual Fees for a given set of weights.
    """
    securities = request.securities
    n_days = len(securities[0].returns)
    
    # Portfolio daily returns series
    returns_matrix = np.array([s.returns for s in securities])
    port_returns = np.dot(weights, returns_matrix)
    
    # Date duration in years
    if request.years is not None:
        Y = request.years
    else:
        Y = n_days / 252.0 if n_days > 500 else n_days / 12.0

    # Cumulative Return
    cum_ret = np.prod(1 + port_returns) - 1
    
    # CAGR (Geometric Return)
    cagr_val = (cum_ret + 1) ** (1 / Y) - 1 if Y > 0 else 0.0
    
    # Volatility (Annualized standard deviation)
    freq = 252 if n_days > 500 else 12
    vol_val = np.std(port_returns, ddof=0) * np.sqrt(freq)
    
    # Expected Return (Arithmetic mean return annualized)
    exp_ret = np.mean(port_returns) * freq
    
    # Sharpe Ratio: using CAGR (geometric mean) as the return in excess of risk-free rate
    # Sharpe = (CAGR - RF) / Vol
    # Let's use a risk-free rate of 1.75% (or 0.0175) to align with testfol.io / US 3M Treasury
    rf = 0.0175
    sharpe_val = (cagr_val - rf) / vol_val if vol_val > 0 else 0.0
    
    # Max Drawdown
    cum_growth = np.cumprod(1 + port_returns)
    peaks = np.maximum.accumulate(cum_growth)
    drawdowns = (cum_growth - peaks) / peaks
    max_dd = np.min(drawdowns) if len(drawdowns) > 0 else 0.0
    
    # Dividend Yield
    div_yield = sum(weights[i] * (securities[i].dividend_yield or 0.0) for i in range(len(securities)))
    
    # Annual Fees (Mapping standard expense ratios for funds)
    FEE_MAPPING = {
        "IEFA": 0.07,
        "SPY": 0.09,
        "GLD": 0.40,
        "AGG": 0.03,
        "VEA": 0.05
    }
    annual_fees = sum(weights[i] * FEE_MAPPING.get(securities[i].ticker.upper(), 0.0) for i in range(len(securities))) / 100.0
    
    return {
        "annual_fees": round(annual_fees * 100, 2),
        "cagr": round(cagr_val * 100, 2),
        "cumulative_return": round(cum_ret * 100, 2),
        "expected_return": round(exp_ret * 100, 2),
        "volatility": round(vol_val * 100, 2),
        "sharpe_ratio": round(sharpe_val, 2),
        "max_drawdown": round(max_dd * 100, 2),
        "dividend_yield": round(div_yield * 100, 2)
    }

def _calculate_tracking_error(opt_weights, curr_weights, securities):
    """
    Calculates tracking error between optimized and current portfolio.
    """
    returns_matrix = np.array([s.returns for s in securities])
    curr_returns = np.dot(curr_weights, returns_matrix)
    opt_returns = np.dot(opt_weights, returns_matrix)
    diff = opt_returns - curr_returns
    n_days = len(diff)
    freq = 252 if n_days > 500 else 12
    te = np.std(diff, ddof=1) * np.sqrt(freq)
    return round(te * 100, 2)