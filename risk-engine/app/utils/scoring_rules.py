def get_risk_level(score):

    if score <= 20:
        return "Low"
    elif score <= 40:
        return "Medium"
    elif score <= 60:
        return "High"
    else:
        return "Critical"