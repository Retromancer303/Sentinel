"""
Unit tests for analytics service.
"""
import pytest
from app.services.analytics import generate_analytics


class TestAnalytics:
    """UC-ANALYTICS-01: Generate analytics from risk data."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_critical_risk_analytics(self):
        """NF-01: Score >= 70 produces critical risk analytics with high business impact."""
        risk_data = {
            "overall_score": 75,
            "categories": {"Network": 80, "Endpoint": 70},
        }
        result = generate_analytics(risk_data)
        assert result["risk_trend_analysis"] == (
            "Risk levels are critically high and require immediate action."
        )
        assert result["business_impact"]["estimated_financial_loss"] == 100000
        assert result["business_impact"]["downtime_risk"] == "High"

    def test_moderate_risk_analytics(self):
        """NF-02: Score 40-69 produces moderate risk analytics."""
        risk_data = {
            "overall_score": 50,
            "categories": {"Network": 60, "Endpoint": 40},
        }
        result = generate_analytics(risk_data)
        assert result["risk_trend_analysis"] == (
            "Risk levels are moderate and should be monitored closely."
        )
        assert result["business_impact"]["estimated_financial_loss"] == 50000
        assert result["business_impact"]["downtime_risk"] == "Medium"

    def test_low_risk_analytics(self):
        """NF-03: Score < 40 produces stable/low risk analytics."""
        risk_data = {
            "overall_score": 25,
            "categories": {"Network": 30, "Endpoint": 20},
        }
        result = generate_analytics(risk_data)
        assert result["risk_trend_analysis"] == "Risk levels are currently stable."
        assert result["business_impact"]["estimated_financial_loss"] == 10000
        assert result["business_impact"]["downtime_risk"] == "Low"

    def test_highest_category_identified(self):
        """NF-04: Analytics correctly identifies the highest-risk category."""
        risk_data = {
            "overall_score": 50,
            "categories": {
                "Network": 30,
                "Endpoint": 80,
                "Application": 45,
            },
        }
        result = generate_analytics(risk_data)
        assert result["highest_risk_category"]["category"] == "Endpoint"
        assert result["highest_risk_category"]["score"] == 80

    def test_average_score_calculated(self):
        """NF-05: Average category score is correctly calculated."""
        risk_data = {
            "overall_score": 50,
            "categories": {"A": 40, "B": 60},
        }
        result = generate_analytics(risk_data)
        assert result["average_category_score"] == 50.0

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_boundary_70_is_critical(self):
        """AF-01: Score of exactly 70 falls in critical range."""
        risk_data = {
            "overall_score": 70,
            "categories": {"X": 70},
        }
        result = generate_analytics(risk_data)
        assert result["business_impact"]["downtime_risk"] == "High"

    def test_boundary_40_is_moderate(self):
        """AF-02: Score of exactly 40 falls in moderate range."""
        risk_data = {
            "overall_score": 40,
            "categories": {"X": 40},
        }
        result = generate_analytics(risk_data)
        assert result["business_impact"]["downtime_risk"] == "Medium"

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_single_category(self):
        """EF-01: Analytics works with a single category."""
        risk_data = {
            "overall_score": 30,
            "categories": {"Solo": 30},
        }
        result = generate_analytics(risk_data)
        assert result["highest_risk_category"]["category"] == "Solo"
        assert result["average_category_score"] == 30.0
