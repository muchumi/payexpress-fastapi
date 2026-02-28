from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL="sqlite:///./payexpress.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

"""
    Creating session factory.
    SessionLocal creates a real database session that allows us to insert, query, update and delete data.Allows interaction with the database.
"""
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Parent class for all models.
Base = declarative_base()

# Safely providing DB session to routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

