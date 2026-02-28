from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.db.database import engine, Base, get_db
from app.models.user import User
from app.core.security import hash_password, verify_password

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
    # normalizing email 
    user_email=user.email.strip().lower()
    # check if the user already exists
    existent_user = db.query(User).filter(User.email == user_email).first()
    if existent_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    # Hashing our password
    hashed_password = hash_password(user.password)
    new_user = User(email=user_email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# User login route
@app.post("/login", status_code=status.HTTP_200_OK)
def login_user(form_data:  OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # normalizing email
    user_email=form_data.username.strip().lower()
    # fetch user from database
    user = db.query(User).filter(User.email == user_email).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"message": f"welcome {user.email}!"}
