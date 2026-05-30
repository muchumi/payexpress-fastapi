from pydantic import BaseModel, ConfigDict
from decimal import Decimal

# Processes response data for wallet information, such as balance and id.
class WalletResponse(BaseModel):
    id: int
    balance: Decimal
    # required to return SQLAlchemy models
    model_config=ConfigDict(from_attributes = True)
        