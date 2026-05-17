from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.walletResponse import WalletResponse

# Creating pydantic models to validate request and response data

# Request body for creating a user
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Response model (does not return password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    wallet: WalletResponse
    # required to return SQLAlchemy models inform of JSON response
    model_config=ConfigDict(from_attributes = True)
