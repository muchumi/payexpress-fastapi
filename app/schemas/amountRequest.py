from pydantic import BaseModel, Field
from typing import Optional

class AmountRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The amount to be processed must be greater than zero")
    currency: str = "KES" #Default currency set to kenyan shillings
    description: Optional[str] = None