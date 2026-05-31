# Portfolio Optimizer API

This repository implements a Portfolio Optimizer REST API.

Endpoints

- `POST /optimize` — JSON request with strategy, securities, optional constraints, and optional factor_returns.
- `POST /optimize/upload` — Multipart form upload: Excel file with securities and optional `factor_file` Excel for factor returns.

Excel input format (for `/optimize/upload`)
- Required columns: `ticker`, `security_name`, `current_weight`.
- One or more return columns (e.g., `r_2020_01`, `r_2020_02`, ...).
- Optional column: `dividend_yield`.

Supported strategies (use `strategy` name):
- `equal_weight`
- `risk_parity`
- `minimize_volatility`
- `minimize_drawdown`
- `max_sharpe`
- `optimize_factor_exposure` (requires a `factor_file` upload and `factor_targets` in constraints)

Constraints

The request accepts an optional `constraints` object with fields:
- `min_weight`, `max_weight`
- `min_cagr`, `volatility_min`, `volatility_max`, `max_drawdown`, `min_dividend_yield`
- `factor_targets`: dictionary where keys are factor names and values are `max` or `min`.

Factor exposure

If a factor file is provided (Excel) with factor return columns, the API will return estimated factor betas for the current and optimized portfolios under the `factor_betas` field in the response.

Running locally

Install dependencies (see `requirements.txt`) and start the FastAPI app (example):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Notes

- The optimizer assumes return series are aligned across securities and factors (same length/order).
- The `optimize_factor_exposure` strategy currently supports specifying factor targets via `constraints.factor_targets`.
- Example Excel files and tests can be added to the `test/` folder.
