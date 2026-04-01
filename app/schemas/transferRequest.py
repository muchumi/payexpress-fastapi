from pydantic import BaseModel, Field
from typing import Literal

class TransferRequest(BaseModel):
    recipient_email: str = Field(..., description="Email of the user to whom the amount will be transferred")
    amount: float = Field(..., gt=0, description="Amount to transfer must be greater than zero")
    currency: Literal["KES", "USD", "EUR"] = Field(default="KES", description="Currency codes allowed: KES, USD, EUR")
    description: str = Field(default="", description="Optional transaction description")

    