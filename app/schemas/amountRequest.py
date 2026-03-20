from pydantic import BaseModel

class AmountRequest(BaseModel):
    amount: float