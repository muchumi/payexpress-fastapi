from pydantic import BaseModel

# Processes response data for wallet information, such as balance and id.
class WalletResponse(BaseModel):
    id: int
    balance: float

    class Config:
        # required to return SQLAlchemy models
        from_attributes=True