# Database configuration — creates the SQLAlchemy engine and session factory.
# The DATABASE_URL can be overridden via environment variable for different environments.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default to SQLite for zero-setup portability. The .db file auto-creates in the project folder.
# Override with DATABASE_URL env var for PostgreSQL (e.g. "postgresql://user:pass@host/dbname").
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./sentinel.db",
)

# SQLite needs connect_args for thread safety; PostgreSQL ignores them.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# SessionLocal is a factory that creates new database sessions.
# autocommit=False means changes must be explicitly committed.
# autoflush=False means changes are not automatically flushed before queries.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """Yield a database session and close it when the request is done.

    Used as a FastAPI dependency: db: Session = Depends(get_db).
    The try/finally ensures the session is closed even if the request raises an error.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()