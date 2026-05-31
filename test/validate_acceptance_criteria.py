"""
Validation script to check API responses against acceptance criteria.
Run after executing the six test scenarios to verify compliance.
"""

import json
import sys
from typing import Dict, List, Any, Tuple

class ValidationChecker:
    """Validates API responses against acceptance criteria."""
    
    TOLERANCE = 0.001  # 0.1% tolerance for floating-point comparisons
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def check_weights_sum_to_100(self, weights: List[float], case_num: int) -> Tuple[bool, str]:
        """Verify that optimized weights sum to 100% (within tolerance)."""
        total = sum(weights)
        if abs(total - 100.0) < 0.001:  # Within 0.001% for floating point
            return True, f"✓ Weights sum to {total:.4f}% (within tolerance)"
        return False, f"✗ Weights sum to {total:.4f}% (expected 100%)"
    
    def check_no_negative_weights(self, weights: List[float], case_num: int) -> Tuple[bool, str]:
        """Verify that no optimized weight is negative."""
        min_weight = min(weights)
        if min_weight >= -self.TOLERANCE:
            return True, f"✓ All weights non-negative (minimum: {min_weight:.6f}%)"
        return False, f"✗ Found negative weight: {min_weight:.6f}%"
    
    def check_security_bounds(self, response: Dict[str, Any], min_w: float = None, max_w: float = None) -> Tuple[bool, str]:
        """Verify that each security respects min/max weight constraints."""
        if min_w is None and max_w is None:
            return True, "✓ No security-level bounds specified"
        
        issues = []
        for security in response.get('allocation_changes', []):
            opt_weight = security.get('optimized_weight', 0.0)
            
            if min_w is not None and opt_weight < (min_w * 100 - self.TOLERANCE):
                issues.append(f"{security.get('ticker')}: {opt_weight:.4f}% < min {min_w * 100:.4f}%")
            
            if max_w is not None and opt_weight > (max_w * 100 + self.TOLERANCE):
                issues.append(f"{security.get('ticker')}: {opt_weight:.4f}% > max {max_w * 100:.4f}%")
        
        if not issues:
            return True, f"✓ All securities within bounds (min: {min_w*100 if min_w else 'N/A'}%, max: {max_w*100 if max_w else 'N/A'}%)"
        
        return False, "✗ Security bounds violated:\n  " + "\n  ".join(issues)
    
    def check_dividend_yield_constraint(self, response: Dict[str, Any], min_yield: float = None) -> Tuple[bool, str]:
        """Verify portfolio-level dividend yield constraint."""
        if min_yield is None:
            return True, "✓ No dividend yield constraint specified"
        
        portfolio_metrics = response.get('portfolio_metrics', {})
        opt_yield = portfolio_metrics.get('optimized_portfolio', {}).get('dividend_yield', 0.0)
        
        # Convert to percentage if needed
        if opt_yield < 1:  # Assume it's in decimal form
            opt_yield = opt_yield * 100
        
        if opt_yield >= (min_yield * 100 - self.TOLERANCE):
            return True, f"✓ Portfolio dividend yield {opt_yield:.4f}% >= required {min_yield*100:.4f}%"
        
        return False, f"✗ Portfolio dividend yield {opt_yield:.4f}% < required {min_yield*100:.4f}%"
    
    def check_required_fields(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Verify response contains all required fields."""
        issues = []
        
        # Check allocation_changes
        if 'allocation_changes' not in response:
            issues.append("Missing 'allocation_changes'")
        else:
            for security in response['allocation_changes']:
                required = ['ticker', 'security_name', 'current_weight', 'optimized_weight', 'allocation', 'change']
                for field in required:
                    if field not in security:
                        issues.append(f"Missing '{field}' in allocation_changes")
        
        # Check portfolio_metrics
        if 'portfolio_metrics' not in response:
            issues.append("Missing 'portfolio_metrics'")
        else:
            metrics_keys = ['current_portfolio', 'optimized_portfolio']
            for key in metrics_keys:
                if key not in response['portfolio_metrics']:
                    issues.append(f"Missing '{key}' in portfolio_metrics")
        
        if issues:
            return False, issues
        return True, []
    
    def check_factor_betas(self, response: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify factor betas are present in response (for Case 6)."""
        required_factors = ['momentum', 'size', 'value']
        
        if 'factor_betas' not in response:
            return False, "✗ Missing 'factor_betas' in response"
        
        factor_data = response['factor_betas']
        
        missing = []
        for factor in required_factors:
            if factor not in factor_data:
                missing.append(factor)
        
        if missing:
            return False, f"✗ Missing factor betas: {', '.join(missing)}"
        
        # Check that current and optimized are present
        for factor in required_factors:
            factor_info = factor_data.get(factor, {})
            if 'current' not in factor_info or 'optimized' not in factor_info:
                return False, f"✗ Factor '{factor}' missing 'current' or 'optimized' beta"
        
        return True, "✓ All factor betas present and correctly structured"
    
    def validate_case_1(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 1: Basic equal-weight sanity check."""
        case_name = "Case 1: Basic Equal-Weight Sanity Check"
        checks = []
        
        # Extract weights
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 1)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 1)))
        
        # Check equal allocation (each should be ~50% for 2 assets)
        if len(weights) == 2:
            is_equal = all(abs(w - 50.0) < 0.1 for w in weights)
            status = (is_equal, "✓ Equal allocation confirmed (~50% each)" if is_equal else "✗ Not equally allocated")
            checks.append(("Equal Allocation", status))
        
        return self._format_results(case_name, checks)
    
    def validate_case_2(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 2: Risk-based allocation (Risk Parity)."""
        case_name = "Case 2: Risk Parity"
        checks = []
        
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 2)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 2)))
        
        return self._format_results(case_name, checks)
    
    def validate_case_3(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 3: Minimize volatility."""
        case_name = "Case 3: Minimize Volatility"
        checks = []
        
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 3)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 3)))
        
        # Check volatility improved
        metrics = response.get('portfolio_metrics', {})
        current_vol = metrics.get('current_portfolio', {}).get('volatility', 0.0)
        optimized_vol = metrics.get('optimized_portfolio', {}).get('volatility', 0.0)
        
        if optimized_vol <= (current_vol + self.TOLERANCE):
            checks.append(("Volatility Reduced", (True, f"✓ Volatility: {current_vol:.4f}% → {optimized_vol:.4f}%")))
        else:
            checks.append(("Volatility Reduced", (False, f"✗ Volatility increased: {current_vol:.4f}% → {optimized_vol:.4f}%")))
        
        return self._format_results(case_name, checks)
    
    def validate_case_4(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 4: Maximize Sharpe Ratio."""
        case_name = "Case 4: Maximize Sharpe Ratio"
        checks = []
        
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 4)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 4)))
        
        # Check Sharpe ratio improved
        metrics = response.get('portfolio_metrics', {})
        current_sharpe = metrics.get('current_portfolio', {}).get('sharpe_ratio', 0.0)
        optimized_sharpe = metrics.get('optimized_portfolio', {}).get('sharpe_ratio', 0.0)
        
        if optimized_sharpe >= (current_sharpe - self.TOLERANCE):
            checks.append(("Sharpe Ratio Improved", (True, f"✓ Sharpe: {current_sharpe:.4f} → {optimized_sharpe:.4f}")))
        else:
            checks.append(("Sharpe Ratio Improved", (False, f"✗ Sharpe decreased: {current_sharpe:.4f} → {optimized_sharpe:.4f}")))
        
        return self._format_results(case_name, checks)
    
    def validate_case_5(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 5: Maximize Sharpe with Constraints."""
        case_name = "Case 5: Maximize Sharpe with Constraints"
        checks = []
        
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 5)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 5)))
        checks.append(("Security Weight Bounds", self.check_security_bounds(response, min_w=0.05, max_w=0.40)))
        checks.append(("Dividend Yield Constraint", self.check_dividend_yield_constraint(response, min_yield=0.025)))
        
        return self._format_results(case_name, checks)
    
    def validate_case_6(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Case 6: Maximize Momentum Factor Exposure (Bonus)."""
        case_name = "Case 6: Maximize Momentum Factor Exposure (BONUS)"
        checks = []
        
        weights = [s['optimized_weight'] for s in response.get('allocation_changes', [])]
        
        checks.append(("Required Fields", self.check_required_fields(response)))
        checks.append(("Weights Sum to 100%", self.check_weights_sum_to_100(weights, 6)))
        checks.append(("No Negative Weights", self.check_no_negative_weights(weights, 6)))
        checks.append(("Factor Betas Present", self.check_factor_betas(response)))
        
        # Check momentum improved
        factor_data = response.get('factor_betas', {})
        current_momentum = factor_data.get('momentum', {}).get('current', 0.0)
        optimized_momentum = factor_data.get('momentum', {}).get('optimized', 0.0)
        
        if optimized_momentum >= (current_momentum - self.TOLERANCE):
            checks.append(("Momentum Maximized", (True, f"✓ Momentum: {current_momentum:.4f} → {optimized_momentum:.4f}")))
        else:
            checks.append(("Momentum Maximized", (False, f"✗ Momentum decreased: {current_momentum:.4f} → {optimized_momentum:.4f}")))
        
        return self._format_results(case_name, checks)
    
    def _format_results(self, case_name: str, checks: List[Tuple[str, Tuple[bool, Any]]]) -> Dict[str, Any]:
        """Format validation results."""
        all_passed = all(check[1][0] for check in checks)
        
        if all_passed:
            self.passed += 1
        else:
            self.failed += 1
        
        return {
            "case": case_name,
            "passed": all_passed,
            "checks": [
                {
                    "name": check[0],
                    "status": "✓ PASS" if check[1][0] else "✗ FAIL",
                    "details": check[1][1] if isinstance(check[1][1], str) else check[1][1]
                }
                for check in checks
            ]
        }


def validate_all_cases(response_file: str = "validation_responses.json"):
    """Validate all six test cases from stored responses."""
    try:
        with open(response_file, 'r') as f:
            responses = json.load(f)
    except FileNotFoundError:
        print(f"Error: {response_file} not found")
        print("Please run: python test/run_validation_cases.py > validation_responses.json")
        return False
    
    checker = ValidationChecker()
    results = []
    
    # Validate each case
    case_validators = [
        checker.validate_case_1,
        checker.validate_case_2,
        checker.validate_case_3,
        checker.validate_case_4,
        checker.validate_case_5,
        checker.validate_case_6,
    ]
    
    for i, validator in enumerate(case_validators, 1):
        case_key = f"case_{i}"
        if case_key in responses:
            results.append(validator(responses[case_key]))
        else:
            print(f"Warning: {case_key} not found in responses file")
    
    # Print results
    print("\n" + "="*70)
    print("PORTFOLIO OPTIMIZER VALIDATION RESULTS")
    print("="*70 + "\n")
    
    for result in results:
        print(f"\n{result['case']}")
        print("-" * 70)
        
        for check in result['checks']:
            print(f"  {check['name']:.<50} {check['status']}")
            if isinstance(check['details'], str):
                print(f"    {check['details']}")
            elif isinstance(check['details'], list):
                for detail in check['details']:
                    print(f"    - {detail}")
        
        overall = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"  {'Overall':.<50} {overall}\n")
    
    # Summary
    print("="*70)
    print(f"SUMMARY: {checker.passed} passed, {checker.failed} failed out of {checker.passed + checker.failed} cases")
    print("="*70 + "\n")
    
    return checker.failed == 0


if __name__ == '__main__':
    success = validate_all_cases()
    sys.exit(0 if success else 1)
