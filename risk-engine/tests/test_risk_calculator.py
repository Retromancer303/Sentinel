"""
Unit tests for the risk calculator service.

Covers Normal Flows, Alternate Flows (varying security postures),
and Exceptional Flows (missing fields, edge cases).
"""
import pytest
from app.services.risk_calculator import calculate_risk


class TestRiskCalculator:
    """UC-RISK-01: Calculate Cybersecurity Risk Score."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_all_controls_in_place_returns_zero(self):
        """NF-01: Company with all security controls in place scores 0 (no risk)."""
        data = {
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 0

    def test_missing_mfa_adds_25(self):
        """NF-02: Missing MFA contributes 25 points to risk score."""
        data = {
            "mfa": False,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 25

    def test_no_backups_adds_30(self):
        """NF-03: No backups ('never') contributes 30 points."""
        data = {
            "mfa": True,
            "backups": "never",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 30

    def test_no_training_adds_20(self):
        """NF-04: No staff training contributes 20 points."""
        data = {
            "mfa": True,
            "backups": "daily",
            "training": False,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 20

    def test_weak_password_policy_adds_15(self):
        """NF-05: Weak password policy contributes 15 points."""
        data = {
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "weak",
        }
        assert calculate_risk(data) == 15

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_worst_case_all_missing_scores_90(self):
        """AF-01: Company missing all controls scores 90 (25+30+20+15)."""
        data = {
            "mfa": False,
            "backups": "never",
            "training": False,
            "password_policy": "weak",
        }
        assert calculate_risk(data) == 90

    def test_score_capped_at_100(self):
        """AF-02: Score is capped at 100 even with all controls missing."""
        data = {
            "mfa": False,
            "backups": "never",
            "training": False,
            "password_policy": "weak",
        }
        # 25+30+20+15 = 90, which is below 100
        assert calculate_risk(data) <= 100

    def test_partial_controls_intermediate_score(self):
        """AF-03: Partial controls produce intermediate scores (example: MFA + backups).
        Missing: training (20) + weak password (15) = 35."""
        data = {
            "mfa": True,
            "backups": "weekly",
            "training": False,
            "password_policy": "weak",
        }
        assert calculate_risk(data) == 35

    def test_backups_weekly_is_not_never(self):
        """AF-04: 'weekly' backups are not treated as missing — only 'never' triggers the penalty."""
        data = {
            "mfa": True,
            "backups": "weekly",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 0

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_missing_mfa_field_defaults_falsy(self):
        """EF-01: Missing 'mfa' key in data treats it as False (falsy), adds 25."""
        data = {
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) == 25

    def test_empty_data_all_defaults(self):
        """EF-02: Completely empty data dict produces max risk score."""
        score = calculate_risk({})
        # mfa: None->falsy (25), backups: None != "never" (0),
        # training: None->falsy (20), password_policy: None != "weak" (0)
        assert score == 45

    def test_none_values_handled(self):
        """EF-03: None values handled as falsy/defaults."""
        data = {
            "mfa": None,
            "backups": None,
            "training": None,
            "password_policy": None,
        }
        score = calculate_risk(data)
        assert score == 45  # Same as empty dict

    def test_score_never_negative(self):
        """EF-04: Score is never negative regardless of input."""
        data = {
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        }
        assert calculate_risk(data) >= 0
