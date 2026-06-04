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
    
# TDD test for transaction history pagination
def test_get_transactions_history_pagination():
    # Creating user and logging in
    create_user()
    token=login_user()
    for i in range(15):
        client.post("/wallets/me/deposit",
            json={
                "amount": 1000
            },
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    response=client.get("/wallets/me/transactions?page=1&limit=10", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==200
    data=response.json()
    assert len(data["data"])==10
    assert data["page"]==1
    assert data["limit"]==10
    assert data["total"]==15
    
# TDD test for transaction filtering by type
def test_filter_transactions_by_type():
    # Creating user and logging in
    create_user()
    token=login_user()
    
    #Deposit
    client.post("/wallets/me/deposit",
        json={
            "amount": 1000
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    # Withdraw
    client.post("/wallets/me/withdraw",
        json={
            "amount": 300
        },
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    response=client.get("/wallets/me/transactions?transaction_type=deposit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code==200
    data=response.json()
    
    assert data["total"]==1
    assert len(data["data"])==1
    assert data["data"][0]["transaction_type"]=="deposit"
    
# TDD test for a user to view his transactions only
def test_user_can_view_own_transactions_only():
    # Create userA and login
    create_user("usera@example.com", "password123")
    token_a=login_user("usera@example.com", "password123")
    
    client.post("/wallets/me/deposit", json={"amount": 1000}, headers={"Authorization": f"Bearer {token_a}"})
    
    # Create userB 
    create_user("userb@example.com", "password123")
    token_b=login_user("userb@example.com", "password123")
    
    client.post("/wallets/me/deposit", json={"amount": 500}, headers={"Authorization": f"Bearer {token_b}"})
    
    # Fetching user A transactions
    response=client.get("/wallets/me/transactions", headers={"Authorization": f"Bearer {token_a}"})
    data=response.json()
    assert response.status_code==200
    assert data["total"]==1
    assert data["data"][0]["amount"]=="1000.00"
    
# TDD test for empty transaction history
def test_get_empty_transaction_history():
    create_user()
    token = login_user()

    response = client.get(
        "/wallets/me/transactions",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 0
    assert data["data"] == []
    
# TDD test for invalid transaction type filter
def test_filter_transactions_invalid_type():
    create_user()
    token = login_user()

    response = client.get(
        "/wallets/me/transactions?transaction_type=invalid",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422