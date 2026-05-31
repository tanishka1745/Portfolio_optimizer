# Portfolio Optimizer API - Validation Guide for Candidates

This guide walks you through validating your Portfolio Optimizer API implementation against the reference live tool.

---

## Quick Start (3 Steps)

### Step 1: Start Your API Server
```powershell
$env:PYTHONPATH="."
venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
✓ API will be available at `http://127.0.0.1:8000`  
✓ Swagger docs at `http://127.0.0.1:8000/docs`

### Step 2: Run Validation Test Cases (New Terminal)
```powershell
$env:PYTHONPATH="."
venv\Scripts\python test/run_validation_cases.py
```
✓ Runs all 6 test scenarios  
✓ Saves responses to `validation_responses.json`

### Step 3: Run Acceptance Criteria Checker
```powershell
$env:PYTHONPATH="."
venv\Scripts\python test/validate_acceptance_criteria.py
```
✓ Validates responses against all acceptance criteria  
✓ Generates detailed pass/fail report

---

## Detailed Validation Workflow

### Understanding the Test Cases

All six test cases are defined in `test/validation_test_cases.json` with:
- Input portfolios and constraints
- Expected behaviors
- Specific acceptance criteria for each case

#### Test Case Reference

| Case | Title | Strategy | # Assets | Constraints |
|------|-------|----------|----------|------------|
| 1 | Equal Weight | `equal_weight` | 2 | None |
| 2 | Risk Parity | `risk_parity` | 2 | None |
| 3 | Min Volatility | `minimize_volatility` | 3 | None |
| 4 | Max Sharpe | `max_sharpe` | 5 | None |
| 5 | Max Sharpe + Constraints | `max_sharpe` | 5 | Min yield 2.5%, security bounds 5-40% |
| 6 | Momentum (Bonus) | `optimize_factor_exposure` | 5 | Maximize Momentum |

---

### Acceptance Criteria for Each Case

#### Case 1: Equal-Weight Sanity Check
**Input**: IEFA 25%, SPY 75%  
**Expected Output**: Both at 50%

```
✓ Weights sum to 100%
✓ No negative weights
✓ Equal allocation (~50% each)
✓ Floating-point error < 0.1%
```

#### Case 2: Risk Parity
**Input**: VEA 25%, AGG 75%  
**Expected Output**: Rebalanced for equal risk contribution

```
✓ Weights sum to 100%
✓ No negative weights
✓ Risk contributions approximately equal
✓ Floating-point error < 0.1%
```

#### Case 3: Minimize Volatility
**Input**: SPY 60%, AGG 30%, GLD 10%  
**Expected Output**: Minimum variance portfolio

```
✓ Weights sum to 100%
✓ No negative weights
✓ Optimized volatility ≤ current volatility
✓ Floating-point error < 0.1%
```

#### Case 4: Maximize Sharpe Ratio
**Input**: 20% each (IEFA, GLD, AGG, VEA, SPY)  
**Expected Output**: Sharpe ratio maximized

```
✓ Weights sum to 100%
✓ No negative weights
✓ Optimized Sharpe ≥ current Sharpe
✓ Floating-point error < 0.1%
```

#### Case 5: Max Sharpe with Constraints
**Input**: 20% each (IEFA, GLD, AGG, VEA, SPY)  
**Constraints**: Min yield 2.5%, security bounds 5-40%

```
✓ Weights sum to 100%
✓ No negative weights
✓ Each security: 5% ≤ weight ≤ 40%
✓ Portfolio dividend yield ≥ 2.5%
✓ Optimized Sharpe ≥ current Sharpe
✓ If infeasible: HTTP 400 with error message
✓ Floating-point error < 0.1%
```

#### Case 6: Momentum Factor Exposure (Bonus)
**Input**: 20% each (IEFA, GLD, AGG, VEA, SPY)  
**Constraint**: Maximize Momentum

```
✓ Weights sum to 100%
✓ No negative weights
✓ Response includes factor_betas
✓ Factor betas: momentum, size, value (lowercase)
✓ Optimized momentum ≥ current momentum
✓ Floating-point error < 0.1%
```

---

## Understanding the Output

### API Response Structure

Every response includes:

#### 1. Allocation Changes
```json
{
  "allocation_changes": [
    {
      "ticker": "SPY",
      "security_name": "SPDR S&P 500 ETF",
      "current_weight": 60.0,
      "optimized_weight": 45.5,
      "allocation": 45.5,
      "change": -14.5,
      "min_weight": 5.0,
      "max_weight": 40.0
    }
  ]
}
```

#### 2. Portfolio Metrics
```json
{
  "portfolio_metrics": {
    "current_portfolio": {
      "cagr": 12.5,
      "volatility": 14.2,
      "sharpe_ratio": 0.88,
      ...
    },
    "optimized_portfolio": {
      "cagr": 13.1,
      "volatility": 13.8,
      "sharpe_ratio": 0.95,
      ...
    },
    "change": {...}
  }
}
```

#### 3. Factor Betas (Case 6 Only)
```json
{
  "factor_betas": {
    "momentum": {
      "current": 0.52,
      "optimized": 0.68
    },
    "size": {...},
    "value": {...}
  }
}
```

---

## Comparing Against Live Tool

### Step-by-Step Comparison

1. **Open the Live Tool**
   - Navigate to the reference Portfolio Optimizer URL
   - Ensure you have the same data loaded (same securities, same time period)

2. **For Each Test Case:**
   - Find the API response in `validation_responses.json` (Case 1 → `case_1`, etc.)
   - Submit the same inputs to the live tool
   - Take a screenshot of the live tool's optimized weights
   - Compare your API weights with the live tool's weights

3. **Verify Acceptance Criteria**
   - Weights sum to 100% ✓
   - Constraints respected ✓
   - Metrics improved (if applicable) ✓
   - Floating-point tolerance < 0.1% ✓

4. **Record Findings**
   - Note any significant differences (>0.1%)
   - Document expected vs. actual values
   - Investigate any constraint violations

---

## Automated Validation

### Using `validate_acceptance_criteria.py`

This script validates responses programmatically:

```powershell
python test/validate_acceptance_criteria.py
```

**Output Example:**
```
════════════════════════════════════════════════════════════════════════════════
PORTFOLIO OPTIMIZER VALIDATION RESULTS
════════════════════════════════════════════════════════════════════════════════

Case 1: Basic Equal-Weight Sanity Check
────────────────────────────────────────────────────────────────────────────────
  Required Fields.................................................................✓ PASS
    ✓ All required fields present
  Weights Sum to 100%.............................................................✓ PASS
    ✓ Weights sum to 100.0000% (within tolerance)
  No Negative Weights.............................................................✓ PASS
    ✓ All weights non-negative (minimum: 0.000000%)
  Equal Allocation.................................................................✓ PASS
    ✓ Equal allocation confirmed (~50% each)
  Overall..........................................................................✓ PASS

[... more cases ...]

════════════════════════════════════════════════════════════════════════════════
SUMMARY: 6 passed, 0 failed out of 6 cases
════════════════════════════════════════════════════════════════════════════════
```

---

## Troubleshooting

### Issue: `validation_responses.json` not found
**Solution**: Run `python test/run_validation_cases.py` first to generate it

### Issue: API returns 400 error for Case 5
**Expected**: This may be correct if constraints are infeasible  
**Check**: Look for clear error message explaining constraint conflict

### Issue: Weights don't sum to 100%
**Investigate**: 
- Check for rounding in optimization solver
- Verify constraint satisfaction in all cases
- Compare with reference tool

### Issue: Weights differ from live tool by >0.1%
**Investigate**:
- Different data sources (Yahoo Finance vs. proprietary)?
- Different time periods for returns?
- Different optimization solver convergence?
- Check calculation of covariance matrix and expected returns

---

## Submission Requirements

For your submission, provide:

### For Each Test Case (1-6):
1. **API Response JSON** - Full response from your `/optimize` endpoint
2. **Screenshot** - Live tool output for the same inputs
3. **Comparison** - Are weights within 0.1%? Notes on any differences

### Summary Document:
- ✓ All 6 cases pass acceptance criteria
- ✓ All weights match reference tool within 0.1% (or documented differences explained)
- ✓ No constraint violations (Case 5 especially)
- ✓ Factor betas included (Case 6)

### Test Evidence:
- Output from `validate_acceptance_criteria.py` showing all cases PASSED
- Screenshots or PDFs showing live tool results

---

## Key Metrics to Track

### For Portfolio Metrics Comparison:
- **CAGR**: Compound annual growth rate
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Return per unit of risk
- **Max Drawdown**: Worst peak-to-trough decline
- **Dividend Yield**: Weighted average yield of portfolio
- **Tracking Error**: Deviation from current portfolio

### For Factor Metrics (Case 6):
- **Momentum Beta**: Exposure to momentum factor
- **Size Beta**: Exposure to size factor (SMB)
- **Value Beta**: Exposure to value factor (HML)

---

## FAQ

**Q: What if my API can't load data from Yahoo Finance?**  
A: Use a local `Data.xlsx` file with your securities and returns. The API will load from Excel first.

**Q: Can I use different securities than the test cases?**  
A: The test cases are standardized - use the exact same securities (IEFA, SPY, VEA, AGG, GLD) for fair comparison.

**Q: Is the 0.1% tolerance strict?**  
A: Yes - it accounts for floating-point rounding. Differences larger than 0.1% indicate an algorithm or data issue.

**Q: What if Case 5 constraints are infeasible?**  
A: Your API should return HTTP 400 with a clear error message explaining why constraints can't be satisfied.

**Q: Do I need to submit Case 6?**  
A: Only if attempting the bonus Factor Exposure feature. Cases 1-5 are required.

---

## Success Criteria

✓ All 6 cases produce valid responses (weights sum to 100%, no negatives)  
✓ Acceptance criteria validation report shows 100% pass rate  
✓ Optimized weights match live tool within 0.1%  
✓ Constraints properly enforced (especially Case 5)  
✓ Factor betas included (Case 6, if attempted)  
✓ Clear error handling for infeasible scenarios  

**With these criteria met, your implementation is ready for production!**
