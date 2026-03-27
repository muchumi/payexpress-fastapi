import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.schemas.tokenResponse import TokenResponse
from app.schemas.walletResponse import WalletResponse
from app.schemas.amountRequest import AmountRequest
from app.schemas.walletTransactionResponse import WalletTransactionResponse
from app.db.database import engine, Base, get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.models.walletTransaction import WalletTransaction
from app.core.security import hash_password, verify_password
from app.auth import create_access_token
from app.dependencies import get_current_user

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
    hashed_password = hash_password(user.password.strip())
    new_user = User(email=user_email, password=hashed_password)
    db.add(new_user)
    db.flush()  # flush to get the new user's ID before committing to database
    
    # automatically creates a wallet for the new registered user
    wallet = Wallet(user_id=new_user.id)
    db.add(wallet)
    db.commit()
    db.refresh(new_user)
    return new_user

# User login route
@app.post("/auth/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_user(form_data:  OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # normalizing email
    user_email=form_data.username.strip().lower()
    # fetch user from database
    user = db.query(User).filter(User.email == user_email).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")

# protected route
@app.get("/users/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


# protected route to get the wallet details of the logged in user
@app.get("/wallets/me", response_model=WalletResponse, status_code=status.HTTP_200_OK)
def read_wallet(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet resource not found")
    return wallet

# deposit route
@app.post("/wallets/me/deposit", response_model=WalletTransactionResponse, status_code=status.HTTP_201_CREATED)
def deposit(request: AmountRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if request.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Deposit amount must be greater than zero")
    wallet=db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    
    try:
        if not wallet:
            wallet = Wallet(user_id=current_user.id, balance=0)
            db.add(wallet)
            db.flush()

        # the wallet balance should be never be null value.If its null it will be considered as 0.
        wallet.balance = (wallet.balance or 0) + request.amount

        transaction = WalletTransaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            transaction_type="deposit"
        )
        db.add(transaction)
        db.commit()
        db.refresh(wallet)
        db.refresh(transaction)
    except Exception as e:
        logging.exception(f"Deposit error")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                        detail="An error occurred while processing your transaction, please try again later")

    return WalletTransactionResponse(
        message= f"Successfully deposited {request.amount} to your wallet",
        amount= request.amount,
        currency= request.currency,
        description= request.description,
        balance= wallet.balance,
        transaction_type= transaction.transaction_type,
        timestamp=transaction.timestamp
    )
    

