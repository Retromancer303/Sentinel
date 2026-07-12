# Scoring rules — maps a numeric risk score to a human-readable risk level.


def get_risk_level(score):
    """Map a numeric risk score (0-100) to a human-readable risk level.

    Thresholds: Low (0-20), Medium (21-40), High (41-60), Critical (61-100).
    """
    if score <= 20:
        return "Low"
    elif score <= 40:
        return "Medium"
    elif score <= 60:
        return "High"
    else:
        return "Critical"