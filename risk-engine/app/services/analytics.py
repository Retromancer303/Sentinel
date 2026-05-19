from datetime import datetime


def generate_analytics(risk_data):
    """
    Generates analytics insights from calculated risk data
    """

    overall_score = risk_data["overall_score"]
    categories = risk_data["categories"]

    # -----------------------------
    # Highest Risk Category
    # -----------------------------
    highest_category = max(categories, key=categories.get)
    highest_score = categories[highest_category]

    # -----------------------------
    # Average Category Score
    # -----------------------------
    average_score = sum(categories.values()) / len(categories)

    # -----------------------------
    # Risk Trend Interpretation
    # -----------------------------
    if overall_score >= 70:
        trend = "Risk levels are critically high and require immediate action."

    elif overall_score >= 40:
        trend = "Risk levels are moderate and should be monitored closely."

    else:
        trend = "Risk levels are currently stable."

    # -----------------------------
    # Business Impact Estimate
    # -----------------------------
    if overall_score >= 70:
        estimated_loss = 100000
        downtime_risk = "High"

    elif overall_score >= 40:
        estimated_loss = 50000
        downtime_risk = "Medium"

    else:
        estimated_loss = 10000
        downtime_risk = "Low"

    # -----------------------------
    # Analytics Response
    # -----------------------------
    analytics = {
        "generated_at": datetime.utcnow().isoformat(),

        "overall_score": overall_score,

        "highest_risk_category": {
            "category": highest_category,
            "score": highest_score
        },

        "average_category_score": round(average_score, 2),

        "risk_trend_analysis": trend,

        "business_impact": {
            "estimated_financial_loss": estimated_loss,
            "downtime_risk": downtime_risk
        }
    }

    return analytics