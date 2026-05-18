from fastapi import APIRouter
from app.services.risk_calculator import calculate_risk
from app.utils.scoring_rules import get_risk_level
from app.services.recommendations import generate_recommendations

router = APIRouter()

@router.post("/calculate-risk")
def risk_endpoint(data: dict):

    score = calculate_risk(data)
    level = get_risk_level(score)
    recommendations = generate_recommendations(data, score)

    return {
        "risk_score": score,
        "risk_level": level,
        "recommendations": recommendations
    }