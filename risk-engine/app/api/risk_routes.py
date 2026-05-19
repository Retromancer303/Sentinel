from fastapi import APIRouter
from app.db.database import SessionLocal
from app.db.repository import save_assessment

router = APIRouter()


@router.post("/calculate-risk")
def calculate_risk(data: dict):

    db = SessionLocal()

    result = {
        "company_name": data["company_name"],
        "overall_score": 72,
        "risk_level": "High"
    }

    save_assessment(db, result)

    return result