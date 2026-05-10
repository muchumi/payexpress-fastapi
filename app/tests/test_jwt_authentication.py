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

client = TestClient(app)

# Create user helper function
def create_user(email="test@example.com", password="strongpassword"):
    return client.post("/users", json={
        "email": email,
        "password": password
    })
  
  
def test_get_current_user_profile():
    create_user()

    login_response = client.post(
        "/auth/login",
        data={
            "username": "test@example.com",
            "password": "strongpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "test@example.com"