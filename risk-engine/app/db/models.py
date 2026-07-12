# SQLAlchemy ORM models — defines the database tables and their columns.
# Each class maps to one table. SQLAlchemy uses these to generate SQL automatically.

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base

# Base is the base class all ORM models inherit from.
# SQLAlchemy uses it to track which classes are tables.
Base = declarative_base()


def _utcnow():
    """Return the current UTC time. Used as the default for created_at columns."""
    return datetime.now(timezone.utc)


class RiskAssessment(Base):
    """Stores the result of a company risk assessment calculation."""
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    overall_score = Column(Integer)
    risk_level = Column(String)
    created_at = Column(DateTime, default=_utcnow)


class ChatMemory(Base):
    """Stores individual chat messages for conversation history."""
    __tablename__ = "chat_memory"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, default="default")
    role = Column(String)          # "user" or "assistant"
    content = Column(Text)         # the message text
    created_at = Column(DateTime, default=_utcnow)