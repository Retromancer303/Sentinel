# API routes — defines the HTTP endpoints the frontend calls.
# Each route uses Pydantic models for request validation and FastAPI's
# dependency injection (Depends) to manage database sessions automatically.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.repository import get_recent_chat_history, save_assessment, save_chat_message
from app.schema.risk_schema import ChatRequest, ChatResponse, RiskAssessmentRequest, RiskAssessmentResponse
from app.services.ai_agent import get_ai_reply
from app.services.analytics import generate_analytics
from app.services.recommendations import generate_recommendations
from app.services.risk_calculator import calculate_risk
from app.utils.scoring_rules import get_risk_level

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(data: ChatRequest, db: Session = Depends(get_db)):
    """Handle a chat message from the user.

    Flow: save user message -> fetch recent history -> call AI -> save assistant reply -> return reply.
    The session_id groups messages belonging to the same conversation.
    """
    message = data.message.strip()
    if not message:
        return ChatResponse(reply="Please enter a cybersecurity question.", session_id=data.session_id)

    # Persist the user's message so it appears in future history lookups.
    save_chat_message(db, data.session_id, "user", message)
    history = get_recent_chat_history(db, data.session_id, limit=6)

    # Get AI reply (tries Ollama/OpenAI/Anthropic depending on config, falls back to keywords).
    reply = get_ai_reply(message, history=history)
    save_chat_message(db, data.session_id, "assistant", reply)
    return ChatResponse(reply=reply, session_id=data.session_id)


@router.post("/calculate-risk", response_model=RiskAssessmentResponse)
def calculate_risk_endpoint(data: RiskAssessmentRequest, db: Session = Depends(get_db)):
    """Calculate cybersecurity risk for a company.

    Runs the full risk pipeline: score calculation -> risk level mapping -> recommendations.
    Persists the assessment and returns the complete result to the caller.
    """
    # Step 1: Calculate raw score from the company's security posture data.
    score = calculate_risk(data.model_dump())

    # Step 2: Map the numeric score to a human-readable level (Low/Medium/High/Critical).
    level = get_risk_level(score)

    # Step 3: Generate actionable recommendations based on the data and score.
    recommendations = generate_recommendations(data.model_dump(), score)

    # Step 4: Save the assessment to the database for future reference.
    save_assessment(db, {
        "company_name": data.company_name,
        "overall_score": score,
        "risk_level": level,
    })

    return RiskAssessmentResponse(
        company_name=data.company_name,
        overall_score=score,
        risk_level=level,
        recommendations=recommendations,
    )