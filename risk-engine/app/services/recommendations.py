def generate_recommendations(data, score):

    recommendations = []

    if not data.get("mfa"):
        recommendations.append("Enable Multi-Factor Authentication (MFA)")

    if data.get("backups") == "never":
        recommendations.append("Implement regular automated backups")

    if not data.get("training"):
        recommendations.append("Provide cybersecurity awareness training")

    if score > 60:
        recommendations.append("Conduct full security audit immediately")

    return recommendations