from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.db.database import engine, Base, get_db
from app.models.user import User

app=FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Root route
@app.get("/", status_code=status.HTTP_200_OK)
def root():
    return {"message": "PayExpress API running"}

# User registration route
@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # check if the user already exists
    existent_user = db.query(User).filter(User.email == user.email).first()
    if existent_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    new_user = User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



