# Risk calculator — scores a company's cybersecurity posture (0-100).
# Higher score = higher risk. The weights reflect how much each missing
# control contributes to overall risk based on common industry heuristics.


def calculate_risk(data):
    """Calculate a cybersecurity risk score (0-100) from a company's security posture.

    Each missing or weak control adds to the score:
    - No MFA (+25): MFA is the single most effective control against account takeover.
    - No backups (+30): Lack of tested backups makes ransomware recovery impossible.
    - No staff training (+20): Untrained staff are the primary entry point for phishing.
    - Weak password policy (+15): Weak passwords enable credential-based attacks.

    Returns the score, capped at 100.
    """
    score = 0

    if not data.get("mfa"):
        score += 25

    if data.get("backups") == "never":
        score += 30

    if not data.get("training"):
        score += 20

    if data.get("password_policy") == "weak":
        score += 15

    return min(score, 100)