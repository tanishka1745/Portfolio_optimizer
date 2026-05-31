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


## API Endpoints

### 1. `POST /optimize` (JSON Payload)

**Request Example - Minimize Volatility:**
```json
{
  "strategy": "risk parity",
  "securities": [
    {
      "ticker": "SPY",
      "security_name": "State Street SPDR S&P 500 ETF Trust",
      "allocation": 60.0,
      "min_weight": 0.0,
      "max_weight": 100.0
    },
    {
      "ticker": "AGG",
      "security_name": "iShares Core US Aggregate Bond ETF",
      "allocation": 40.0,
      "min_weight": 0.0,
      "max_weight": 100.0
    }
  ]
}
```

**Response Example:**
```json
{
  "optimization_strategy": "minimize_volatility",
  "allocation_changes": [
    {
      "ticker": "SPY",
      "security_name": "SPDR S&P 500 ETF",
      "current_weight": 60,
      "optimized_weight": 20.09,
      "change": -39.91,
      "min_weight": 5,
      "max_weight": 60
    },
    {
      "ticker": "AGG",
      "security_name": "iShares Core US Aggregate Bond ETF",
      "current_weight": 30,
      "optimized_weight": 61.09,
      "change": 31.09,
      "min_weight": 10,
      "max_weight": 70
    },
    {
      "ticker": "GLD",
      "security_name": "SPDR Gold Shares",
      "current_weight": 10,
      "optimized_weight": 18.83,
      "change": 8.83,
      "min_weight": 5,
      "max_weight": 40
    }
  ],
  "factor_betas": {
    "current_portfolio": {
      "momentum": 0.11411761219446463,
      "size": -0.12197888822240849,
      "value": 0.1102779313720765
    },
    "optimized_portfolio": {
      "momentum": 0.053304390229500835,
      "size": -0.03653513855702767,
      "value": 0.00891026959301534
    }
  }
}
```
## Automated Error Handling
If any constraints are incompatible or impossible to meet (e.g. demanding a 10% dividend yield when no assets yield more than 4%), the API will reject the request immediately with an **HTTP 400 Bad Request** error containing details about the infeasible constraints.


#ScreenShot of correct output

Equal Weight <br>
<img width="691" height="163" alt="output" src="https://github.com/user-attachments/assets/16ac8521-f983-4b77-9a52-486a4cf1a259" />
<img width="818" height="206" alt="response data" src="https://github.com/user-attachments/assets/03759a3f-add6-4d72-84fa-6ee964d0e271" />
<img width="870" height="266" alt="api request" src="https://github.com/user-attachments/assets/66cb688f-6fb4-463f-a4e3-c61bfaf9dac6" />

<br>

# Risk Parity
<img width="697" height="239" alt="risk correct " src="https://github.com/user-attachments/assets/6c459a79-5699-43db-bd0e-0fce34a9db0a" />
<img width="909" height="257" alt="response risky" src="https://github.com/user-attachments/assets/28df59fe-a210-481b-aaa0-bfad24b32ac2" />
<img width="902" height="290" alt="request risky" src="https://github.com/user-attachments/assets/1d4aa593-0c72-4bd8-8299-21d9b298a0ac" />


