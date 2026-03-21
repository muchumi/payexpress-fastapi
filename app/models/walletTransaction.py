from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KES")
    description = Column(String, nullable=True)
    transaction_type = Column(String, nullable=False)  # "deposit", "withdraw", "transfer"
    timestamp = Column(DateTime, default=datetime.utcnow)

    # relationships (optional)
    user = relationship("User", back_populates="transactions")
    wallet = relationship("Wallet", back_populates="transactions")