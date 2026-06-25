import json
import os

from sqlalchemy.exc import OperationalError

from app.db.models import ChatMemory, RiskAssessment

_in_memory_chat_store = {}


def _get_redis_client():
    try:
        import redis
    except ImportError:
        return None

    try:
        client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def save_assessment(db, data):

    assessment = RiskAssessment(
        company_name=data["company_name"],
        overall_score=data["overall_score"],
        risk_level=data["risk_level"]
    )

    db.add(assessment)

    db.commit()

    db.refresh(assessment)

    return assessment


def save_chat_message(db, session_id: str, role: str, content: str):
    client = _get_redis_client()
    if client is not None:
        key = f"chat:{session_id}"
        client.rpush(key, json.dumps({"role": role, "content": content}))
        client.ltrim(key, -6, -1)
        return {"role": role, "content": content}

    if db is not None:
        try:
            message = ChatMemory(session_id=session_id, role=role, content=content)
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except OperationalError:
            db.rollback()

    _in_memory_chat_store.setdefault(session_id, []).append({"role": role, "content": content})
    return {"role": role, "content": content}


def get_recent_chat_history(db, session_id: str, limit: int = 6):
    client = _get_redis_client()
    if client is not None:
        raw_items = client.lrange(f"chat:{session_id}", -limit, -1)
        history = []
        for item in raw_items:
            try:
                record = json.loads(item)
            except json.JSONDecodeError:
                continue
            history.append({"role": record.get("role", "user"), "content": record.get("content", "")})
        return history

    if db is not None:
        try:
            rows = (
                db.query(ChatMemory)
                .filter(ChatMemory.session_id == session_id)
                .order_by(ChatMemory.created_at.asc())
                .limit(limit)
                .all()
            )
            return [{"role": row.role, "content": row.content} for row in rows]
        except OperationalError:
            db.rollback()

    return list(_in_memory_chat_store.get(session_id, []))[-limit:]