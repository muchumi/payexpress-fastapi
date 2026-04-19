from sqlalchemy import Column, DateTime, Integer, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from decimal import Decimal

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Numeric(12,2), default=Decimal("0.00"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    user = relationship("User", back_populates="wallet")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())