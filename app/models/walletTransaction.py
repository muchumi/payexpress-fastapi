from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(18,2), nullable=False)
    currency = Column(String, default="KES")
    description = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False)  # "deposit", "withdraw", "transfer"
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    status=Column(String, default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationships to user and wallet
    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="transactions")