import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load connection string from environment variable (best practice)
# Example: "postgresql://user:password@host:port/dbname"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fastapi_user:password@localhost:5432/fastapi_db")

# 1. SQLAlchemy Engine
# The engine is the starting point for all SQLAlchemy applications.
# It manages the connection pool and dialect.
engine = create_engine(
    DATABASE_URL,
    # Only needed for SQLite to handle concurrent requests
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 2. SessionLocal
# This factory creates individual database sessions. Each request should
# get its own session (a unit of work) to ensure thread safety.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Declarative Base
# This base class is inherited by all your SQLAlchemy ORM models.
# It links the ORM models to the SQLAlchemy engine.
Base = declarative_base()

def get_db():
    """
    Dependency that yields a database session for a single request,
    and ensures the session is closed afterward.
    """
    db = SessionLocal()
    try:
        # The session is yielded to the route handler (Service/Repository)
        yield db
    finally:
        # Ensures the session is closed even if an exception occurs
        db.close()