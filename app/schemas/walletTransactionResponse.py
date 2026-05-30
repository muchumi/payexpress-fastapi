from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class WalletTransactionResponse(BaseModel):
    message: str
    amount: Decimal
    currency: str
    description: Optional[str] = None
    balance: Decimal
    transaction_type: str  # "deposit", "withdraw", "transfer"
    timestamp: datetime
    model_config=ConfigDict(from_attributes = True)