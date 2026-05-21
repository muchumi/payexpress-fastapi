import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.wallet import Wallet
from app.models.walletTransaction import WalletTransaction

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
client=TestClient(app)

# Create user helper function
def create_user(email="test@example.com", password="strongpassword"):
    return client.post("/users", json={
        "email": email,
        "password": password
    })

# Create login user helper function
def login_user(email="test@example.com", password="strongpassword"):
    response=client.post("/auth/login", data={
        "username": email,
        "password": password
    })  
    return response.json()["access_token"] 


# Test for automatic wallet creation upon user registration
def test_wallet_creation_on_user_registration():
    response=create_user()
    
    assert response.status_code==201
    data=response.json()
    assert "wallet" in data
    assert data["wallet"]["balance"]==0.0
    
# Test for wallet deposit operations
def test_deposit_transaction():
    create_user()
    token=login_user()
    response=client.post("/wallets/me/deposit", json={
        "amount": 1000
        },
        headers={
            "Authorization": f"Bearer {token}"
        }                   
    )
    assert response.status_code==201
    data=response.json()
    assert data["balance"]==1000.0
      
    # Verifying database state after deposit transaction
    db = SessionLocal()
    wallet=db.query(Wallet).first()
    assert wallet is not None
    assert float(wallet.balance)==1000.0
    transaction=db.query(WalletTransaction).first()
    assert transaction is not None
    assert float(transaction.amount)==1000.0
    assert transaction.transaction_type=="deposit"
    db.close()
    
# Test for wallet withdrawal operations
def test_withdrawal_transaction():
    create_user()
    token=login_user()
    # First deposit to ensure sufficient balance for withdrawal
    client.post("/wallets/me/deposit", 
                json={
                    "amount": 1000
                },
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
    # Withdraw money
    response=client.post("/wallets/me/withdraw", 
                json={
                    "amount": 350
                },
                headers={
                    "Authorization": f"Bearer {token}"
                }
            )
    assert response.status_code==201
    data=response.json()
    assert data["balance"]==650.0
    #Verifying database state after withdrawal transaction
    db=SessionLocal()
    wallet=db.query(Wallet).first()
    assert wallet is not None
    assert float(wallet.balance)==650.0
    transactions=db.query(WalletTransaction).all()
    assert len(transactions)==2
    withdraw_transaction=transactions[1]
    assert float(withdraw_transaction.amount)==350.0
    assert withdraw_transaction.transaction_type=="withdrawal"
    db.close()
    
# Test for withdrawal wallet operation with insufficient funds
def test_withdrawal_with_insufficient_funds():
    create_user()
    token=login_user()
    
    # Small amount deposit
    client.post("/wallets/me/deposit", 
        json={
            "amount": 100
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    # Attempting overdraft withdrawal
    response=client.post("/wallets/me/withdraw", 
        json={
            "amount": 200
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    assert response.status_code==400
    data=response.json()
    assert data["detail"] == "Insufficient funds"
    
    # Verifying wallet balance remains unchanged
    db=SessionLocal()
    wallet=db.query(Wallet).first()
    assert wallet is not None
    assert float(wallet.balance)==100.0
    
    # Verifying no withdrawal transaction was created
    transactions=db.query(WalletTransaction).all()
    assert len(transactions)==1
    assert transactions[0].transaction_type=="deposit"
    db.close()
    
    
    