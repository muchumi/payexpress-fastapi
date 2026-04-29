import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_user():
    response=client.post("/users", json={
        "email": "test@example.com", 
        "password": "strongpassword"
    })
    assert respon