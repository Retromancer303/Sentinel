from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String)
    overall_score = Column(Integer)
    risk_level = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)