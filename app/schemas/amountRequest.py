from pydantic import BaseModel, Field
from typing import Optional

class AmountRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The amount to be processed must be greater than zero")
    currency: str = Field(default="KES", description="The default currency of the amount set to KES") 
    description: Optional[str] = None
    