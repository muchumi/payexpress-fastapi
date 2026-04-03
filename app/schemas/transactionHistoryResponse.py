from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionHistoryResponse(BaseModel):
    id: int
    amount: float
    currency: str
    description: Optional[str]=None
    transaction_type: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes=True
