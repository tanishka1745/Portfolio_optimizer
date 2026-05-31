from pydantic import BaseModel
from typing import Optional, List

class Security(BaseModel):
    ticker: str

class Constraints(BaseModel):
    min_weight: Optional[float] = 0

class OptimizationRequest(BaseModel):
    strategy: str
    securities: List[Security]
    constraints: Optional[Constraints] = None

print(OptimizationRequest.model_fields)
print(OptimizationRequest.model_fields["constraints"])
