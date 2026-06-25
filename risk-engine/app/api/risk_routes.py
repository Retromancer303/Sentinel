from fastapi import APIRouter
from app.db.database import SessionLocal
from app.db.repository import get_recent_chat_history, save_assessment, save_chat_message
from app.services.ai_agent import get_ai_reply

router = APIRouter()


def build_chat_reply(message: str, history: list[dict] | None = None) -> str:
    return get_ai_reply(message, history=history)


@router.post("/chat")
def chat(data: dict):
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not message:
        return {"reply": "Please enter a cybersecurity question."}

    db = SessionLocal()
    try:
        save_chat_message(db, session_id, "user", message)
        history = get_recent_chat_history(db, session_id, limit=6)

        reply = build_chat_reply(message, history=history)
        save_chat_message(db, session_id, "assistant", reply)
        return {"reply": reply, "session_id": session_id}
    finally:
        db.close()


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