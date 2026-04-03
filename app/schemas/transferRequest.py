from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class TransferRequest(BaseModel):
    recipient_email: str = Field(..., description="Email of the user to whom the amount will be transferred")
    amount: float = Field(..., gt=0, description="Amount to transfer must be greater than zero")
    currency: Literal["KES", "USD", "EUR"] = Field(default="KES", description="Currency codes allowed: KES, USD, EUR")
    description: Optional[str]=None

    @field_validator("recipient_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()



    