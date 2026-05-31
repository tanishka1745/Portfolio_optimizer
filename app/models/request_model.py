from pydantic import BaseModel, model_validator
from typing import List, Optional, Dict

class Security(BaseModel):
    ticker: str
    security_name: str
    current_weight: Optional[float] = None
    allocation: Optional[float] = None
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None
    returns: Optional[List[float]] = None
    dividend_yield: Optional[float] = None

    @model_validator(mode='before')
    @classmethod
    def normalize_keys(cls, data):
        if isinstance(data, dict):
            # 1. Normalize spaces to underscores, convert to lowercase
            normalized = {}
            for k, v in data.items():
                norm_k = str(k).lower().strip().replace(" ", "_")
                normalized[norm_k] = v

            # 2. Check for security name variation
            for k in list(normalized.keys()):
                if "secu" in k or "name" in k:
                    if k != "security_name":
                        normalized["security_name"] = normalized[k]

            # 3. Check for current_weight and allocation variations
            if "allocation" in normalized:
                normalized["current_weight"] = normalized["allocation"]
            elif "current_weight" in normalized:
                normalized["allocation"] = normalized["current_weight"]

            # 4. Check for min_weight / in_weight / in_wieght / min_wieght
            for k in list(normalized.keys()):
                if "min" in k or "in_w" in k:
                    if k != "min_weight":
                        normalized["min_weight"] = normalized[k]

            # 5. Check for max_weight / max_wieght
            for k in list(normalized.keys()):
                if "max" in k:
                    if k != "max_weight":
                        normalized["max_weight"] = normalized[k]

            return normalized
        return data


class Constraints(BaseModel):
    min_weight: Optional[float] = 0.0
    max_weight: Optional[float] = 1.0
    min_dividend_yield: Optional[float] = None
    factor_targets: Optional[Dict[str, str]] = None
    # Max Sharpe extra constraints
    min_cagr: Optional[float] = None           # e.g. 0.05 = minimum 5% annualized return
    min_volatility: Optional[float] = None     # volatility range lower bound (annualized)
    max_volatility: Optional[float] = None     # volatility range upper bound (annualized)
    max_drawdown: Optional[float] = None       # e.g. -0.20 = max allowed drawdown of -20%

class OptimizationRequest(BaseModel):
    strategy: str
    securities: List[Security]
    constraints: Optional[Constraints] = None
    factor_returns: Optional[Dict[str, List[float]]] = None
    years: Optional[float] = None


