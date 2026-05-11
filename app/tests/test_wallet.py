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
    
# Test for automatic wallet creation upon user registration
def test_wallet_creation_on_user_registration():
    response=create_user()
    
    assert response.status_code==201
    data=response.json()
    assert "wallet" in data
    assert data["wallet"]["balance"]==0.0
    
    