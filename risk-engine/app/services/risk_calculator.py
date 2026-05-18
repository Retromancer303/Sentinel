def calculate_risk(data):

    score = 0

    # Authentication
    if not data.get("mfa"):
        score += 25

    # Backups
    if data.get("backups") == "never":
        score += 30

    # Training
    if not data.get("training"):
        score += 20

    # Password policy
    if data.get("password_policy") == "weak":
        score += 15

    # Cap score at 100
    score = min(score, 100)

    return score