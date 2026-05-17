from pydantic import BaseModel, ConfigDict
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
    model_config=ConfigDict(from_attributes = True)
