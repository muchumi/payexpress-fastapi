from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__="users"

    id=Column(Integer, primary_key=True, index=True)
    email=Column(String, unique=True, index=True)
    password=Column(String)

    wallet = relationship("Wallet", back_populates="user", uselist=False)


