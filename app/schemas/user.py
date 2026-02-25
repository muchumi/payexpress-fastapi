from pydantic import BaseModel, EmailStr

# Creating pydantic models to validate request and response data

# Request body for creating a user
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Response model (does not return password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        # required to return SQLAlchemy models
        orm_mode=True
