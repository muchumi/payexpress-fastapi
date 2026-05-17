from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class WalletTransactionResponse(BaseModel):
    message: str
    amount: float
    currency: str
    description: Optional[str] = None
    balance: float
    transaction_type: str  # "deposit", "withdraw", "transfer"
    timestamp: datetime
    model_config=ConfigDict(from_attributes = True)