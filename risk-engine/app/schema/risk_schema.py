# Pydantic schemas — define the shape of API requests and responses.
# FastAPI uses these to automatically validate incoming JSON and generate API docs.
# If a request doesn't match the schema, FastAPI returns a 422 error with details.

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    """Response body for POST /chat."""
    reply: str
    session_id: str


class RiskAssessmentRequest(BaseModel):
    """Request body for POST /calculate-risk.

    Fields represent the company's current security posture.
    Default values assume the worst case (no controls in place).
    """
    company_name: str
    mfa: bool = False
    backups: str = "never"
    training: bool = False
    password_policy: str = "weak"


class RiskAssessmentResponse(BaseModel):
    """Response body for POST /calculate-risk."""
    company_name: str
    overall_score: int
    risk_level: str
    recommendations: list[str]
