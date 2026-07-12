# Analytics — generates insights and business impact estimates from risk data.

from datetime import datetime, timezone


def generate_analytics(risk_data):
    """Generate analytics insights from calculated risk data.

    Expects risk_data to contain:
    - overall_score: int (0-100)
    - categories: dict mapping category name -> score

    Returns a summary with the highest-risk category, average score,
    a trend interpretation, and estimated business impact.
    """
    overall_score = risk_data["overall_score"]
    categories = risk_data["categories"]

    # Find which category has the highest individual risk score.
    highest_category = max(categories, key=categories.get)
    highest_score = categories[highest_category]
    average_score = sum(categories.values()) / len(categories)

    # Use the overall score to determine trend text and business impact figures.
    # Thresholds: >= 70 is critical, >= 40 is moderate, < 40 is stable.
    if overall_score >= 70:
        trend = "Risk levels are critically high and require immediate action."
        estimated_loss = 100000
        downtime_risk = "High"
    elif overall_score >= 40:
        trend = "Risk levels are moderate and should be monitored closely."
        estimated_loss = 50000
        downtime_risk = "Medium"
    else:
        trend = "Risk levels are currently stable."
        estimated_loss = 10000
        downtime_risk = "Low"

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "highest_risk_category": {
            "category": highest_category,
            "score": highest_score,
        },
        "average_category_score": round(average_score, 2),
        "risk_trend_analysis": trend,
        "business_impact": {
            "estimated_financial_loss": estimated_loss,
            "downtime_risk": downtime_risk,
        },
    }