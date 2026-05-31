from pydantic import BaseModel
from typing import List, Optional, Dict

class Security(BaseModel):
    ticker: str
    security_name: str
    current_weight: float
    returns: Optional[List[float]] = None
    dividend_yield: Optional[float] = None

class Constraints(BaseModel):
    min_weight: Optional[float] = 0.0
    max_weight: Optional[float] = 1.0
    min_dividend_yield: Optional[float] = None
    factor_targets: Optional[Dict[str, str]] = None

class OptimizationRequest(BaseModel):
    strategy: str
    securities: List[Security]
    constraints: Optional[Constraints] = None
    factor_returns: Optional[Dict[str, List[float]]] = None
    years: Optional[float] = None


