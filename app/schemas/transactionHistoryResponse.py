from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

class TransactionHistoryResponse(BaseModel):
    id: int
    amount: Decimal
    currency: str
    description: Optional[str]=None
    transaction_type: str
    status: str
    timestamp: datetime

    class Config:
        from_attributes=True
