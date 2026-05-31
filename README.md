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

## Validation Against Live Portfolio Optimizer Tool

Candidates must validate their API implementation against the live Portfolio Optimizer tool using six standardized test cases. The first five are **required**; Case 6 applies only to candidates attempting the **Factor Exposure bonus**.

### How to Run Validation Tests

#### Step 1: Start the API Server
```powershell
# Terminal 1: Start the FastAPI server
$env:PYTHONPATH="."
venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### Step 2: Run All Six Test Scenarios
```powershell
# Terminal 2: Execute validation test cases
$env:PYTHONPATH="."
venv/Scripts/python test/run_validation_cases.py
```

This generates API responses for all six scenarios. Capture the output or redirect to a JSON file.

#### Step 3: Run Acceptance Criteria Validation
```powershell
# Validate responses against acceptance criteria
$env:PYTHONPATH="."
venv/Scripts/python test/validate_acceptance_criteria.py
```

#### Step 4: Compare Against Live Tool
1. Visit the live Portfolio Optimizer tool
2. For each test case:
   - Submit the same input portfolio and constraints to the live tool
   - Take a screenshot of the optimized weights and metrics
   - Compare with your API response
   - Verify that optimized weights match within **0.1% tolerance**

---

## API Endpoints

### 1. `POST /optimize` (JSON Payload)

**Request Example - Minimize Volatility:**
```json
{
  "strategy": "minimize_volatility",
  "securities": [
    { "ticker": "SPY", "security_name": "SPDR S&P 500 ETF", "current_weight": 60.0, "returns": [0.015, 0.005, 0.020, ...], "dividend_yield": 1.5 },
    { "ticker": "AGG", "security_name": "iShares Core US Aggregate Bond ETF", "current_weight": 30.0, "returns": [0.005, 0.003, 0.001, ...], "dividend_yield": 3.2 },
    { "ticker": "GLD", "security_name": "SPDR Gold Shares", "current_weight": 10.0, "returns": [0.008, 0.002, -0.010, ...], "dividend_yield": 0.0 }
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

**Security Fields:**
- `ticker` (required): Security ticker symbol
- `security_name` (required): Full name of the security
- `current_weight` (required): Current weight as percentage (0-100)
- `returns` (required): Array of historical periodic returns (decimals, e.g., 0.012 = 1.2%)
- `dividend_yield` (optional): Annual dividend yield as percentage

**Optional Constraints:**
- `min_weight`: Global minimum weight per security (percentage)
- `max_weight`: Global maximum weight per security (percentage)
- `min_dividend_yield`: Portfolio minimum dividend yield (percentage)
- `factor_targets`: Factor exposure targets (e.g., `{"Momentum": "max"}`)

---

### 2. `POST /optimize/upload` (Excel File Upload)
Upload a single-sheet or multi-sheet `Data.xlsx`:

**Format:**
- Columns: `ticker`, `security_name`, `current_weight`, `dividend_yield` (optional), plus return columns
- Multi-sheet: Fund Info, Fund Returns, Factor Returns (optional)

**Example cURL:**
```bash
curl -X POST "http://127.0.0.1:8000/optimize/upload" \
  -F "strategy=minimize_volatility" \
  -F "file=@Data.xlsx"
```

---

## Automated Error Handling
If any constraints are incompatible or impossible to meet (e.g. demanding a 10% dividend yield when no assets yield more than 4%), the API will reject the request immediately with an **HTTP 400 Bad Request** error containing details about the infeasible constraints.
