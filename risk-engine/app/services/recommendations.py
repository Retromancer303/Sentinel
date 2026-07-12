# Recommendations — generates actionable security suggestions based on the
# company's security posture and overall risk score.


def generate_recommendations(data, score):
    """Generate security recommendations based on the company's data and risk score.

    Checks each security control and suggests improvements for any that are missing.
    A high overall score (>60) also triggers an urgent audit recommendation.

    Returns a list of actionable recommendation strings.
    """
    recommendations = []

    if not data.get("mfa"):
        recommendations.append("Enable Multi-Factor Authentication (MFA)")

    if data.get("backups") == "never":
        recommendations.append("Implement regular automated backups")

    if not data.get("training"):
        recommendations.append("Provide cybersecurity awareness training")

    # Score > 60 means "Critical" level — flag for an immediate full audit.
    if score > 60:
        recommendations.append("Conduct full security audit immediately")

    return recommendations