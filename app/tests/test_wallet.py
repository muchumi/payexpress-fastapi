import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
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

client = TestClient(app)

# Helper function for user registration and login

def create_user(email="test@example.com", password="strongpassword"):
    return client.post("/users", json={
        "email": email,
        "password": password
    })

def login_user(email="test@example.com", password="strongpassword"):
    response = client.post("/auth/login", data={
        "username": email,
        "password": password
    })
    assert response.status_code == 200
    return response.json()["access_token"]


# Tests
def test_wallet_creation_on_user_registration():
    response = create_user()

    assert response.status_code == 201
    data = response.json()

    assert "wallet" in data
    assert Decimal(str(data["wallet"]["balance"])) == Decimal("0.00")


def test_deposit_transaction():
    create_user()
    token = login_user()

    response = client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()

    assert Decimal(str(data["balance"])) == Decimal("1000.00")

    db = SessionLocal()
    wallet = db.query(Wallet).first()
    transaction = db.query(WalletTransaction).first()

    assert wallet.balance == Decimal("1000.00")
    assert transaction.amount == Decimal("1000.00")
    assert transaction.transaction_type == "deposit"

    db.close()


def test_withdrawal_transaction():
    create_user()
    token = login_user()

    client.post(
        "/wallets/me/deposit",
        json={"amount": 1000},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.post(
        "/wallets/me/withdraw",
        json={"amount": 350},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()

    assert Decimal(str(data["balance"])) == Decimal("650.00")

    db = SessionLocal()
    wallet = db.query(Wallet).first()
    transactions = db.query(WalletTransaction).all()

    deposit_tx = next(t for t in transactions if t.transaction_type == "deposit")
    withdraw_tx = next(t for t in transactions if t.transaction_type == "withdrawal")

    assert wallet.balance == Decimal("650.00")
    assert deposit_tx.amount == Decimal("1000.00")
    assert withdraw_tx.amount == Decimal("350.00")

    db.close()


def test_withdrawal_with_insufficient_funds():
    create_user()
    token = login_user()

    client.post(
        "/wallets/me/deposit",
        json={"amount": 100},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.post(
        "/wallets/me/withdraw",
        json={"amount": 200},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient funds"

    db = SessionLocal()
    wallet = db.query(Wallet).first()
    transactions = db.query(WalletTransaction).all()

    assert wallet.balance == Decimal("100.00")
    assert len(transactions) == 1
    assert transactions[0].transaction_type == "deposit"

    db.close()