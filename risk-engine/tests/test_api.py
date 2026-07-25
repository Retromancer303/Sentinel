"""
API integration tests for Sentinel backend using FastAPI TestClient.

Covers: /chat endpoint, /calculate-risk endpoint, / (health check),
covering Normal, Alternate, and Exceptional flows from use-case descriptions.

Test framework: pytest + FastAPI TestClient
"""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.db.models import Base
from app.db.database import engine
from app.main import app

# Pre-made mock reply so all chat tests run fast (no real AI/network calls).
MOCK_REPLY = "This is a mock response about cybersecurity."


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables before each test, drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def mock_ai():
    """Mock get_ai_reply globally so chat endpoint tests avoid real network calls."""
    with patch("app.api.risk_routes.get_ai_reply", return_value=MOCK_REPLY):
        yield


@pytest.fixture
def client():
    """Return a TestClient that uses a real SQLite database for integration tests."""
    return TestClient(app)


# ── UC-SYSTEM-01: Health Check ──────────────────────────────────────────────


class TestHealthCheck:
    """UC-HEALTH-01: Backend health check endpoint."""

    def test_root_returns_status(self, client):
        """NF-01: GET / returns status indicating the risk engine is running."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Risk engine running"

    def test_root_returns_json_content_type(self, client):
        """NF-02: Response content type is application/json."""
        response = client.get("/")
        assert response.headers["content-type"].startswith("application/json")


# ── UC-CHAT-01: Chat with Sentinel ──────────────────────────────────────────


class TestChatEndpoint:
    """UC-CHAT-01: POST /chat — AI-powered cybersecurity chat."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_chat_returns_reply(self, client):
        """NF-01: Valid chat message returns a non-empty reply."""
        response = client.post("/chat", json={
            "message": "What is phishing?",
            "session_id": "test-session",
        })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert data["session_id"] == "test-session"

    def test_chat_returns_session_id(self, client):
        """NF-02: Response includes the session_id that was sent."""
        response = client.post("/chat", json={
            "message": "How do I enable MFA?",
            "session_id": "my-session",
        })
        assert response.status_code == 200
        assert response.json()["session_id"] == "my-session"

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_chat_default_session_id(self, client):
        """AF-01: Omitting session_id defaults to 'default'."""
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 200
        assert response.json()["session_id"] == "default"

    def test_chat_conversation_context_persists(self, client):
        """AF-02: Messages in same session are stored and context persists."""
        sid = "context-test"

        r1 = client.post("/chat", json={
            "message": "What is ransomware?",
            "session_id": sid,
        })
        assert r1.status_code == 200

        r2 = client.post("/chat", json={
            "message": "How do I defend against it?",
            "session_id": sid,
        })
        assert r2.status_code == 200
        assert len(r2.json()["reply"]) > 0

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_empty_message_returns_error_prompt(self, client):
        """EF-01: Empty or whitespace-only message returns a prompt to enter text."""
        response = client.post("/chat", json={
            "message": "",
            "session_id": "test",
        })
        assert response.status_code == 200
        assert "enter" in response.json()["reply"].lower()

    def test_whitespace_only_message(self, client):
        """EF-02: Whitespace-only message is treated as empty."""
        response = client.post("/chat", json={
            "message": "   ",
            "session_id": "test",
        })
        assert response.status_code == 200
        assert "enter" in response.json()["reply"].lower()

    def test_missing_message_field_returns_422(self, client):
        """EF-03: Missing required 'message' field returns 422 validation error."""
        response = client.post("/chat", json={"session_id": "test"})
        assert response.status_code == 422

    def test_extra_fields_ignored(self, client):
        """EF-04: Extra unknown fields in request body are ignored."""
        response = client.post("/chat", json={
            "message": "Hello",
            "session_id": "test",
            "extra_field": "should be ignored",
        })
        assert response.status_code == 200
        assert "reply" in response.json()

    def test_long_message_accepted(self, client):
        """EF-05: Very long messages (500 chars) are accepted."""
        long_msg = "A" * 500
        response = client.post("/chat", json={
            "message": long_msg,
            "session_id": "test",
        })
        assert response.status_code == 200


# ── UC-RISK-01: Calculate Risk Assessment ───────────────────────────────────


class TestCalculateRiskEndpoint:
    """UC-RISK-01: POST /calculate-risk — cybersecurity risk assessment."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_calculate_risk_low_posture(self, client):
        """NF-01: Company with all controls returns low risk."""
        response = client.post("/calculate-risk", json={
            "company_name": "SecureCorp",
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "SecureCorp"
        assert data["overall_score"] == 0
        assert data["risk_level"] == "Low"
        assert data["recommendations"] == []
        assert data["assessment_id"] is not None  # Persisted to DB

    def test_calculate_risk_high_risk_company(self, client):
        """NF-02: Company missing all controls returns high/critical risk with all recs."""
        response = client.post("/calculate-risk", json={
            "company_name": "Vulnerable Inc.",
            "mfa": False,
            "backups": "never",
            "training": False,
            "password_policy": "weak",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 90
        assert data["risk_level"] == "Critical"
        assert len(data["recommendations"]) == 4  # MFA + backups + training + audit

    def test_calculate_risk_response_structure(self, client):
        """NF-03: Response includes all required fields."""
        response = client.post("/calculate-risk", json={
            "company_name": "TestCo",
        })
        assert response.status_code == 200
        data = response.json()
        required_fields = ["company_name", "overall_score", "risk_level", "recommendations", "assessment_id"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        assert isinstance(data["recommendations"], list)
        assert data["assessment_id"] is not None

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_calculate_risk_default_values(self, client):
        """AF-01: Omitting optional fields uses defaults (worst case)."""
        response = client.post("/calculate-risk", json={
            "company_name": "DefaultCo",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 90
        assert data["risk_level"] == "Critical"

    def test_calculate_risk_partial_controls(self, client):
        """AF-02: Partial controls produce intermediate scores."""
        response = client.post("/calculate-risk", json={
            "company_name": "PartialCorp",
            "mfa": True,
            "backups": "daily",
            "training": False,
            "password_policy": "strong",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 20  # Only training missing
        assert data["risk_level"] == "Low"

    def test_calculate_risk_score_boundary_40(self, client):
        """AF-03: Score of 40 maps to 'Medium' risk level."""
        response = client.post("/calculate-risk", json={
            "company_name": "MediumCorp",
            "mfa": False,
            "backups": "daily",
            "training": True,
            "password_policy": "weak",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 40
        assert data["risk_level"] == "Medium"

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_calculate_risk_missing_company_name_returns_422(self, client):
        """EF-01: Missing required 'company_name' returns 422."""
        response = client.post("/calculate-risk", json={
            "mfa": True,
        })
        assert response.status_code == 422

    def test_calculate_risk_invalid_backups_value_rejected(self, client):
        """EF-02: Invalid backups value is now rejected with 422 (Literal validation added)."""
        response = client.post("/calculate-risk", json={
            "company_name": "Test",
            "backups": "unknown_value",
        })
        assert response.status_code == 422

    def test_calculate_risk_invalid_password_policy_rejected(self, client):
        """EF-02b: Invalid password_policy value is rejected with 422 (Literal validation added)."""
        response = client.post("/calculate-risk", json={
            "company_name": "Test",
            "password_policy": "very_weak",
        })
        assert response.status_code == 422

    def test_calculate_risk_extra_fields_ignored(self, client):
        """EF-03: Extra unknown fields in request are ignored."""
        response = client.post("/calculate-risk", json={
            "company_name": "Test",
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
            "employee_count": 500,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["overall_score"] == 0

    def test_calculate_risk_special_chars_in_company_name(self, client):
        """EF-04: Special characters in company name are accepted."""
        response = client.post("/calculate-risk", json={
            "company_name": "ACME & Sons (2024) Ltd.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "ACME & Sons (2024) Ltd."

    def test_calculate_risk_empty_company_name(self, client):
        """EF-05: Empty company name is accepted (no validation on length)."""
        response = client.post("/calculate-risk", json={
            "company_name": "",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == ""


# ── UC-SYSTEM-02: 404/405 Error Handling ─────────────────────────────────────


class TestErrorHandling:
    """UC-ERROR-01: Error handling for invalid routes and methods."""

    def test_invalid_route_returns_404(self, client):
        """NF-01: GET request to non-existent route returns 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    def test_wrong_method_on_chat_returns_405(self, client):
        """NF-02: GET request to POST-only /chat endpoint returns 405."""
        response = client.get("/chat")
        assert response.status_code == 405

    def test_wrong_method_on_calculate_risk_returns_405(self, client):
        """NF-03: GET request to POST-only /calculate-risk returns 405."""
        response = client.get("/calculate-risk")
        assert response.status_code == 405
