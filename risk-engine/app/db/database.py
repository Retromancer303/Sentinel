# Database configuration — creates the SQLAlchemy engine and session factory.
# The DATABASE_URL can be overridden via environment variable for different environments.

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Falls back to the local PostgreSQL instance if DATABASE_URL is not set.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/cyberrisk",
)

engine = create_engine(DATABASE_URL)

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