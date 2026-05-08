import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.user import User

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
  
 
def test_create_user():
    response = create_user()

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    
# Test for duplicate emails during user creation
def test_create_user_duplicate_email():
    first_response = create_user()
    assert first_response.status_code == 201

    response = create_user()

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"
    
# Test if the password has been hashed in the database
def test_password_is_hashed():
    create_user()
    session=SessionLocal()
    user = session.query(User).filter(User.email == "test@example.com").first()
    assert user.password != "strongpassword"
    
# Test for login/authentication
def test_login_user():
    create_user()
    response=client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "strongpassword"
    })
    assert response.status_code == 200
    data=response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    