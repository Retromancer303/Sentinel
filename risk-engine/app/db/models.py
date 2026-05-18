from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    score = Column(Integer)
    level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)