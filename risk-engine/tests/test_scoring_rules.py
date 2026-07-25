"""
Unit tests for scoring rules (risk level mapping).
"""
import pytest
from app.utils.scoring_rules import get_risk_level


class TestScoringRules:
    """UC-SCORE-01: Map numeric risk score to risk level."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("score,expected", [
        (0, "Low"),
        (10, "Low"),
        (20, "Low"),
    ])
    def test_low_risk_thresholds(self, score, expected):
        """NF-01: Scores 0-20 map to 'Low' risk level."""
        assert get_risk_level(score) == expected

    @pytest.mark.parametrize("score,expected", [
        (21, "Medium"),
        (30, "Medium"),
        (40, "Medium"),
    ])
    def test_medium_risk_thresholds(self, score, expected):
        """NF-02: Scores 21-40 map to 'Medium' risk level."""
        assert get_risk_level(score) == expected

    @pytest.mark.parametrize("score,expected", [
        (41, "High"),
        (50, "High"),
        (60, "High"),
    ])
    def test_high_risk_thresholds(self, score, expected):
        """NF-03: Scores 41-60 map to 'High' risk level."""
        assert get_risk_level(score) == expected

    @pytest.mark.parametrize("score,expected", [
        (61, "Critical"),
        (80, "Critical"),
        (100, "Critical"),
    ])
    def test_critical_risk_thresholds(self, score, expected):
        """NF-04: Scores 61-100 map to 'Critical' risk level."""
        assert get_risk_level(score) == expected

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_boundary_values_correct(self):
        """AF-01: Boundary values map to correct levels.
        20->Low, 21->Medium, 40->Medium, 41->High, 60->High, 61->Critical.
        """
        assert get_risk_level(20) == "Low"
        assert get_risk_level(21) == "Medium"
        assert get_risk_level(40) == "Medium"
        assert get_risk_level(41) == "High"
        assert get_risk_level(60) == "High"
        assert get_risk_level(61) == "Critical"

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_negative_score_defaults_to_low(self):
        """EF-01: Negative scores still map to 'Low' (<= 20 branch)."""
        assert get_risk_level(-5) == "Low"

    def test_above_100_maps_to_critical(self):
        """EF-02: Scores above 100 still map to 'Critical'."""
        assert get_risk_level(150) == "Critical"
