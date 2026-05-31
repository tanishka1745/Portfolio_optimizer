# Portfolio Optimizer REST API

A premium FastAPI-based REST API that implements multiple portfolio optimization strategies (Equal Weight, Risk Parity, Minimize Volatility, Maximize Sharpe Ratio, Minimize Drawdown, and Factor Exposure Optimization) with support for security weight limits, minimum dividend yields, and factor regression.

It automatically interfaces with your custom `Data.xlsx` sheet or dynamically downloads real-time returns from Yahoo Finance and Fama-French Momentum factors from the Kenneth French Data Library.

---

## Features & Supported Strategies

1. **Equal Weight (`equal_weight`)**: Allocates capital equally across all assets ($1/N$).
2. **Risk Parity (`risk_parity`)**: Formulates equal risk contribution using relative risk contributions (RRC), ensuring robust numerical convergence on daily returns.
3. **Minimize Volatility (`minimize_volatility`)**: Finds the global minimum variance portfolio. Supports portfolio-level yield and security-level bounds.
4. **Maximize Sharpe Ratio (`max_sharpe`)**: Maximizes the risk-adjusted return relative to volatility. Supports yield constraints and security-level bounds.
5. **Minimize Drawdown (`minimize_drawdown`)**: Minimizes the maximum drawdown over the historical return series.
6. **Optimize Factor Exposure (`optimize_factor_exposure`)**: Maximizes or minimizes exposure to Fama-French factors (Momentum, Value, Size).

---

## Output Response Format

The API response returns:
1. **Allocation Changes**: Side-by-side comparison of current and optimized weights, including:
   - `ticker`, `security name`, `current_weight`, `optimized_weight`, `allocation` (optimized weight), `change`
   - Security-level bounds: `min weight` and `max weight`
2. **Portfolio Metrics**: Side-by-side comparison of `current_portfolio`, `optimized_portfolio`, and `change` for:
   - CAGR, Volatility, Sharpe Ratio, Cumulative Return, Expected Return, Max Drawdown, Dividend Yield, and Annual Fees.
   - **Tracking Error** between the optimized and current portfolios.
3. **Factor Betas** (Bonus): Lowercase keys (`momentum`, `size`, `value`) containing factor betas for both current and optimized portfolios.

---

## Local Setup & Installation

### Prerequisites
* Python 3.8 or higher installed on your system.

### 1. Clone the repository
```bash
git clone <repository-url>
cd Portfolio_optimizer
```

### 2. Create and Activate a Virtual Environment
**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Running the Web Server
Launch the FastAPI development server:
```bash
uvicorn app.main:app --reload
```
* The API will start running locally at: `http://127.0.0.1:8000`
* You can access the **Swagger Interactive API Documentation** at: `http://127.0.0.1:8000/swagger`

---

## Validating the 6 Test Scenarios

To run the local validation script that executes all six scenarios against your `Data.xlsx` sheet:
```powershell
# Set Python path and run the script
$env:PYTHONPATH="."
venv/Scripts/python test/run_validation_cases.py
```

### Summary of the 6 Validation Scenarios
1. **Scenario 1**: Equal Weights check (IEFA: 25%, SPY: 75% inputs).
2. **Scenario 2**: Risk Parity check (VEA: 25%, AGG: 75% inputs).
3. **Scenario 3**: Minimize Volatility (SPY: 60%, AGG: 30%, GLD: 10% inputs).
4. **Scenario 4**: Maximize Sharpe (20% each: IEFA, GLD, AGG, VEA, SPY).
5. **Scenario 5**: Maximize Sharpe with Constraints (Min yield: 2.50%; Security min: 5%, max: 40%).
6. **Scenario 6**: Momentum Factor Exposure (Maximize Momentum; returns lowercase betas).

---

## API Endpoints

### 1. `POST /optimize` (JSON Payload)
**Request Body:**
```json
{
  "strategy": "max_sharpe",
  "securities": [
    { "ticker": "IEFA", "current_weight": 20.0 },
    { "ticker": "GLD", "current_weight": 20.0 },
    { "ticker": "AGG", "current_weight": 20.0 },
    { "ticker": "VEA", "current_weight": 20.0 },
    { "ticker": "SPY", "current_weight": 20.0 }
  ],
  "constraints": {
    "min_weight": 5.0,
    "max_weight": 40.0,
    "min_dividend_yield": 2.50
  }
}
```

### 2. `POST /optimize/upload` (Excel Upload)
Upload a multi-sheet `Data.xlsx` file matching the structure:
* **Fund Info**: Columns `ticker`, `fund_name`, `dividend_yield`.
* **Fund Returns**: Columns `date`, `total_return`, `ticker`.
* **Factor Returns**: Columns `date`, `total_return`, `index_ticker` (Momentum, Value, Size).

You can pass a `constraints` string parameter as form-data (e.g. `{"min_weight": 5, "max_weight": 40, "min_dividend_yield": 2.5}`).

---

## Automated Error Handling
If any constraints are incompatible or impossible to meet (e.g. demanding a 10% dividend yield when no assets yield more than 4%), the API will reject the request immediately with an **HTTP 400 Bad Request** error containing details about the infeasible constraints.
