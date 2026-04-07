import logging
from datetime import datetime, date
from fastapi import FastAPI, HTTPException, status, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user import UserCreate, UserResponse
from app.schemas.tokenResponse import TokenResponse
from app.schemas.walletResponse import WalletResponse
from app.schemas.amountRequest import AmountRequest
from app.schemas.walletTransactionResponse import WalletTransactionResponse
from app.schemas.transferRequest import TransferRequest
from app.schemas.paginatedTransactionResponse import PaginatedTransactionResponse
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
    
    access_token = create_access_token(data={"sub": str(user.email)})
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

        # the wallet balance should never be a null value.If its null it will be considered as 0.
        wallet.balance = (wallet.balance or 0) + request.amount

        transaction = WalletTransaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            transaction_type="deposit",
            status="complete"
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
    

# withdrawal route
@app.post("/wallets/me/withdraw", response_model=WalletTransactionResponse, status_code=status.HTTP_201_CREATED)
def withdraw(request: AmountRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    wallet = db.query(Wallet).filter(Wallet.user_id==current_user.id).first()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="wallet resource not found")
    current_balance = wallet.balance or 0

    if request.amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Withdrawal amount must be greater than zero")
    
    # preventing overdraft
    if request.amount > current_balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient funds")
    
    try:
        # deducting balance
        wallet.balance = current_balance - request.amount
        # recording the transaction
        transaction = WalletTransaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=request.amount,
            currency=request.currency,
            description=request.description,
            transaction_type="withdrawal",
            status="completed"
        )
        db.add(transaction)
        db.commit()
        db.refresh(wallet)
        db.refresh(transaction)
    except Exception:
        logging.exception("Withdrawal error")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Transaction failed"
        )
    return WalletTransactionResponse(
        message="Withdrawal successful",
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        balance=wallet.balance,
        transaction_type=transaction.transaction_type,
        timestamp=transaction.timestamp
    )

# wallet transfer route
@app.post("/wallets/me/transfer", response_model=WalletTransactionResponse, status_code=status.HTTP_201_CREATED)
def transfer_funds(request: TransferRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetching sender's wallet with locking 
    sender_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).with_for_update().first()
    if not sender_wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender wallet not found")
    
    # Fetching recipient
    recipient=db.query(User).filter(User.email==request.recipient_email).first()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    # Preventing self transfer
    if recipient.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot transfer funds to yourself")
    
    # Fetching recipient's wallet with locking
    recipient_wallet=db.query(Wallet).filter(Wallet.user_id==recipient.id).with_for_update().first()
    if not recipient_wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient wallet not found")
    
    # Checking sender balance
    sender_balance=sender_wallet.balance or 0
    if request.amount > sender_balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance")

    try:
        sender_wallet.balance=sender_balance - request.amount
        recipient_wallet.balance=(recipient_wallet.balance or 0) + request.amount
        debit_transaction = WalletTransaction(
            user_id=current_user.id,
            wallet_id=sender_wallet.id,
            amount=request.amount,
            currency=request.currency,
            description=request.description or f"Transfer to {recipient.email}",
            transaction_type="transfer_debit",
            status="completed"
        )

        credit_transaction=WalletTransaction(
            user_id=recipient.id,
            wallet_id=recipient_wallet.id,
            amount=request.amount,
            currency=request.currency,
            description=request.description or f"Transfer from {current_user.email}",
            transaction_type="transfer_credit",
            status="completed"
        )
        db.add_all([debit_transaction, credit_transaction])
        db.commit()
        db.refresh(sender_wallet)
        db.refresh(debit_transaction)

    except Exception:
        logging.exception("Transfer error")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transfer failed")
    return WalletTransactionResponse(
        message=f"Transferred {request.amount} {request.currency} to {recipient.email}",
        amount=request.amount,
        currency=request.currency,
        description=request.description,
        balance=sender_wallet.balance,
        transaction_type=debit_transaction.transaction_type,
        timestamp=debit_transaction.timestamp
    )

# Transaction history route
@app.get("/wallets/me/transactions", response_model=PaginatedTransactionResponse, status_code=status.HTTP_200_OK)
def transaction_history(
    limit: int = Query(10, le=100), 
    offset: int = Query(0, ge=0), 
    transaction_type : str | None = Query(None, description="Filter by transaction type"),
    start_date: date | None = Query(None, description="Start date for filtering transactions data(YYYY-MM-DD)"),
    end_date : date | None = Query(None, description="End date for filtering transactions data(YYYY-MM-DD)"), 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
    ):
    query = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id)
    total=query.count()
    transactions=query.order_by(WalletTransaction.timestamp.desc()).offset(offset).limit(limit).all()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "data": transactions
    }

