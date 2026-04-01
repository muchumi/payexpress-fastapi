from pydantic import BaseModel, Field, field_validator
from typing import Optional

# Defining allowed currencies for validation
ALLOWED_CURRENCIES = ["KES", "USD", "EUR"]

class AmountRequest(BaseModel):
    amount: float = Field(..., gt=0, description="The amount to be processed must be greater than zero")
    currency: str = Field(default="KES", description="Currency code (e.g. KES, USD, EUR)") 
    description: Optional[str] = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        if value not in ALLOWED_CURRENCIES:
            raise ValueError(f"Unsupported currency.Allowed currencies are: {', '.join(ALLOWED_CURRENCIES)}")
        return value