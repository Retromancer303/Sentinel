from fastapi import APIRouter
from app.db.database import SessionLocal
from app.db.repository import save_assessment

router = APIRouter()


CYBERSECURITY_TOPICS = {
    "phishing": "Phishing risk is reduced with employee training, email filtering, MFA, and a clear reporting process.",
    "password": "Password risk is reduced with long unique passwords, a password manager, MFA, and removing shared accounts.",
    "mfa": "Multi-factor authentication should be enabled for email, VPN, admin panels, cloud services, and financial systems.",
    "backup": "Backups should be encrypted, tested regularly, and stored separately from production systems.",
    "ransomware": "Ransomware defenses include tested backups, patching, endpoint protection, least privilege, and user awareness training.",
    "firewall": "Firewalls should block unnecessary inbound traffic, restrict admin access, and be reviewed regularly.",
    "patch": "Patch management should prioritize internet-facing systems, critical vulnerabilities, operating systems, browsers, and security tools.",
    "risk": "Cyber risk is usually based on likelihood, impact, exposed assets, existing controls, and business criticality.",
}


def build_chat_reply(message: str) -> str:
    question = message.lower()

    for topic, reply in CYBERSECURITY_TOPICS.items():
        if topic in question:
            return reply

    return (
        "I can help with cybersecurity risk questions. Ask about phishing, MFA, "
        "passwords, backups, ransomware, firewalls, patching, or risk scoring."
    )


@router.post("/chat")
def chat(data: dict):
    message = data.get("message", "").strip()

    if not message:
        return {"reply": "Please enter a cybersecurity question."}

    return {"reply": build_chat_reply(message)}


@router.post("/calculate-risk")
def calculate_risk(data: dict):

    db = SessionLocal()

    result = {
        "company_name": data["company_name"],
        "overall_score": 72,
        "risk_level": "High"
    }

    save_assessment(db, result)

    return result