from app.db.models import RiskAssessment


def save_assessment(db, data):

    assessment = RiskAssessment(
        company_name=data["company_name"],
        overall_score=data["overall_score"],
        risk_level=data["risk_level"]
    )

    db.add(assessment)

    db.commit()

    db.refresh(assessment)

    return assessment