import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal

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
      