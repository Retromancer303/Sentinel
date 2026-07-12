# Repository — data access layer that abstracts storage backends.
#
# Chat history uses a three-tier fallback chain:
#   1. Redis (fast, in-memory, trims to last 6 messages per session)
#   2. PostgreSQL via SQLAlchemy (persistent, survives restarts)
#   3. In-memory Python dict (always available, but lost on restart)
#
# Risk assessments go directly to PostgreSQL (no fallback needed —
# the API can still return the result even if persistence fails).

import json
import os

from sqlalchemy.exc import OperationalError

from app.db.models import ChatMemory, RiskAssessment

# Final fallback storage — a plain Python dict held in process memory.
# Cleared whenever the server restarts.
_in_memory_chat_store = {}


def _get_redis_client():
    """Attempt to connect to Redis. Returns None if unavailable.

    Redis is optional — the app works fine without it by falling back
    to PostgreSQL or the in-memory store.
    """
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
    """Save a risk assessment to the database.

    If the database is unavailable, silently skips persistence
    so the API can still return a result to the caller.
    """
    try:
        assessment = RiskAssessment(
            company_name=data["company_name"],
            overall_score=data["overall_score"],
            risk_level=data["risk_level"]
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment
    except OperationalError:
        db.rollback()
        return None


def save_chat_message(db, session_id: str, role: str, content: str):
    """Save a chat message using the best available storage backend.

    Tries Redis first (fast, trims to last 6 messages), then PostgreSQL,
    then falls back to the in-memory dict.
    """
    # Try Redis first — it's the fastest option for chat history.
    client = _get_redis_client()
    if client is not None:
        key = f"chat:{session_id}"
        client.rpush(key, json.dumps({"role": role, "content": content}))
        # Keep only the last 6 messages per session to avoid unbounded growth.
        client.ltrim(key, -6, -1)
        return {"role": role, "content": content}

    # Try PostgreSQL if Redis is unavailable.
    if db is not None:
        try:
            message = ChatMemory(session_id=session_id, role=role, content=content)
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        except OperationalError:
            db.rollback()

    # Final fallback: in-memory dict (data lost on restart).
    _in_memory_chat_store.setdefault(session_id, []).append({"role": role, "content": content})
    return {"role": role, "content": content}


def get_recent_chat_history(db, session_id: str, limit: int = 6):
    """Retrieve recent chat messages for a session.

    Uses the same fallback chain as save_chat_message:
    Redis -> PostgreSQL -> in-memory dict.
    """
    # Try Redis first.
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

    # Try PostgreSQL.
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

    # Final fallback: in-memory dict.
    return list(_in_memory_chat_store.get(session_id, []))[-limit:]