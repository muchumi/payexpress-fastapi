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
    
    
# TDD test for wallet to wallet transfer transactions
def test_wallet_transfer_successful():
    # Creating sender
    create_user("sender@example.com", "password123")
    sender_token=login_user("sender@example.com", "password123")
    
    # Funding sender wallet
    client.post("/wallets/me/deposit", json={"amount": 1000}, headers={"Authorization": f"Bearer {sender_token}"})
    
    # Creating recipient
    create_user("recipient@example.com", "password123")
    
    response=client.post("/wallets/me/transfer", 
        json={
            "recipient_email": "recipient@example.com",
            "amount": 300
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )
    assert response.status_code==201
    
# TDD test for wallet transfer to update both sender and recipient wallet balances   
def test_wallet_transfer_updates_both_wallet_balances():
    # Create sender
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    # Fund sender wallet
    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    # Create recipient
    create_user("recipient@example.com", "password123")
    recipient_token = login_user("recipient@example.com", "password123")

    # Transfer
    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 300
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 201

    # Check sender balance
    sender_wallet = client.get(
        "/wallets/me",
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert sender_wallet.status_code == 200
    assert sender_wallet.json()["balance"] == "700.00"

    # Check recipient balance
    recipient_wallet = client.get(
        "/wallets/me",
        headers={"Authorization": f"Bearer {recipient_token}"}
    )

    assert recipient_wallet.status_code == 200
    assert recipient_wallet.json()["balance"] == "300.00"
    
# TDD test for transfer fails when sender has insufficient funds
def test_wallet_transfer_fails_with_insufficient_balance():
    # Create sender
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    # Deposit only 100
    client.post(
        "/wallets/me/deposit",
        json={"amount": 100},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    # Create recipient
    create_user("recipient@example.com", "password123")

    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 300
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient balance"
    
# TDD test for transfer fails when recipient does not exist/email not found    
def test_wallet_transfer_fails_when_recipient_not_found():
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "unknown@example.com",
            "amount": 300
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipient not found"
    
# TDD test for transfer fails when sender tries to transfer to self
def test_wallet_transfer_to_self_fails():
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")
    client.post("/wallets/me/deposit", json={"amount": 1000}, headers={"Authorization": f"Bearer {sender_token}"})
    response=client.post("/wallets/me/transfer", json={"recipient_email": "sender@example.com", "amount": 300}, headers={"Authorization": f"Bearer {sender_token}"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot transfer funds to yourself"
    
# TDD test for recording wallet transfer transactions
def test_recording_wallet_transfer_transactions():
    # create user
    create_user("sender@example.com", "password123")
    sender_token=login_user("sender@example.com", "password123")
    client.post("/wallets/me/deposit", json={"amount": 1000}, headers={"Authorization": f"Bearer {sender_token}"})
    
    # create recipient
    create_user("recipient@example.com", "password123")
    recipient_token=login_user("recipient@example.com", "password123")
    
    # transfer
    client.post("/wallets/me/transfer", json={"recipient_email": "recipient@example.com", "amount": 300}, headers={"Authorization": f"Bearer {sender_token}"})
    
    # sender transaction history
    sender_history=client.get("/wallets/me/transactions", headers={"Authorization": f"Bearer {sender_token}"})
    
    sender_data=sender_history.json()
    assert sender_data["total"]==2
    assert sender_data["data"][0]["transaction_type"]=="transfer_debit"
    
    # recipient transaction history
    recipient_history=client.get("/wallets/me/transactions", headers={"Authorization": f"Bearer {recipient_token}"})
    recipient_data=recipient_history.json()
    assert recipient_data["total"]==1
    assert recipient_data["data"][0]["transaction_type"]=="transfer_credit"
 
# TDD test for transfer amount must be positive   
def test_wallet_transfer_amount_must_be_positive():
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    create_user("recipient@example.com", "password123")

    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 0
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 422
    
# TDD test for transfer amount must be positive (negative amount should fail)
def test_wallet_transfer_negative_amount_fails():
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    create_user("recipient@example.com", "password123")

    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": -100
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 422
    
# TDD test for transfer requires authentication  
def test_transfer_requires_authentication():
    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 100
        }
    )

    assert response.status_code == 401  
    
# TDD test for transfer transaction details
def test_transfer_transactions_contain_correct_details():
    # Create sender
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    # Create recipient
    create_user("recipient@example.com", "password123")
    recipient_token = login_user("recipient@example.com", "password123")

    # Transfer
    client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 300
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    # Sender history
    sender_history = client.get(
        "/wallets/me/transactions",
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    sender_txn = sender_history.json()["data"][0]

    assert sender_txn["transaction_type"] == "transfer_debit"
    assert sender_txn["amount"] == "300.00"

    # Recipient history
    recipient_history = client.get(
        "/wallets/me/transactions",
        headers={"Authorization": f"Bearer {recipient_token}"}
    )

    recipient_txn = recipient_history.json()["data"][0]

    assert recipient_txn["transaction_type"] == "transfer_credit"
    assert recipient_txn["amount"] == "300.00"
    
# TDD test for transferring entire balance  
def test_wallet_transfer_entire_balance():
    # Create sender
    create_user("sender@example.com", "password123")
    sender_token = login_user("sender@example.com", "password123")

    # Fund sender wallet
    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    # Create recipient
    create_user("recipient@example.com", "password123")
    recipient_token = login_user("recipient@example.com", "password123")

    # Transfer entire balance
    response = client.post(
        "/wallets/me/transfer",
        json={
            "recipient_email": "recipient@example.com",
            "amount": 1000
        },
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert response.status_code == 201

    # Verify sender balance is zero
    sender_wallet = client.get(
        "/wallets/me",
        headers={"Authorization": f"Bearer {sender_token}"}
    )

    assert sender_wallet.status_code == 200
    assert sender_wallet.json()["balance"] == "0.00"

    # Verify recipient received full amount
    recipient_wallet = client.get(
        "/wallets/me",
        headers={"Authorization": f"Bearer {recipient_token}"}
    )

    assert recipient_wallet.status_code == 200
    assert recipient_wallet.json()["balance"] == "1000.00"