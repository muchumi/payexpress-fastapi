from pydantic import BaseModel

class AmountRequest(BaseModel):
    amount: float
    currency: str = "KES" #Default currency set to kenyan shillings
    description: str = None