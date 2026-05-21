import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.walletTransaction import WalletTransaction

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
client = TestClient(app)

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

def test_get_transactions_history():
    # Creating user and logging in
    create_user()
    token=login_user()
    
    client.post("/wallets/me/deposit",
        json={
            "amount": 1000
        },
        headers=
        {
            "Authorization": f"Bearer {token}"
        }
        
    )
    client.post("/wallets/me/withdraw",
        json={
            "amount": 300
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    
    response=client.get("/wallets/me/transactions",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )
    assert response.status_code==200
    data=response.json()
    assert len(data["data"])==2
    assert data["data"][0]["transaction_type"]=="withdrawal"
    assert data["data"][1]["transaction_type"]=="deposit"
    
