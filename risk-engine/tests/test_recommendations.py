"""
Unit tests for the recommendations generator.
"""
import pytest
from app.services.recommendations import generate_recommendations


class TestRecommendations:
    """UC-REC-01: Generate actionable security recommendations."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_no_recommendations_when_all_controls_present(self):
        """NF-01: No recommendations generated when all controls are in place."""
        data = {
            "mfa": True,
            "backups": "daily",
            "training": True,
            "password_policy": "strong",
        }
        recs = generate_recommendations(data, score=10)
        assert recs == []

    def test_missing_mfa_generates_recommendation(self):
        """NF-02: Missing MFA generates 'Enable MFA' recommendation."""
        data = {"mfa": False, "backups": "daily", "training": True}
        recs = generate_recommendations(data, score=25)
        assert "Enable Multi-Factor Authentication (MFA)" in recs

    def test_no_backups_generates_recommendation(self):
        """NF-03: No backups generates backup recommendation."""
        data = {"mfa": True, "backups": "never", "training": True}
        recs = generate_recommendations(data, score=30)
        assert any("backups" in r.lower() for r in recs)

    def test_no_training_generates_recommendation(self):
        """NF-04: No training generates training recommendation."""
        data = {"mfa": True, "backups": "daily", "training": False}
        recs = generate_recommendations(data, score=20)
        assert any("training" in r.lower() for r in recs)

    def test_high_score_adds_audit_recommendation(self):
        """NF-05: Score > 60 adds 'full security audit' recommendation."""
        data = {"mfa": True, "backups": "daily", "training": True}
        recs = generate_recommendations(data, score=75)
        assert any("audit" in r.lower() for r in recs)

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_multiple_missing_controls_generates_multiple_recs(self):
        """AF-01: Multiple missing controls produce multiple recommendations."""
        data = {
            "mfa": False,
            "backups": "never",
            "training": False,
        }
        recs = generate_recommendations(data, score=90)
        assert len(recs) == 4  # MFA + backups + training + audit

    def test_score_exactly_60_no_audit(self):
        """AF-02: Score of exactly 60 (High) does NOT trigger audit recommendation."""
        data = {"mfa": True, "backups": "daily", "training": True}
        recs = generate_recommendations(data, score=60)
        assert not any("audit" in r.lower() for r in recs)

    def test_score_61_triggers_audit(self):
        """AF-03: Score of 61 (Critical) triggers audit recommendation."""
        data = {"mfa": True, "backups": "daily", "training": True}
        recs = generate_recommendations(data, score=61)
        assert any("audit" in r.lower() for r in recs)

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_empty_data_with_high_score(self):
        """EF-01: Empty data with high score still produces audit-only recommendation."""
        recs = generate_recommendations({}, score=80)
        # mfa missing -> False; backups missing -> not "never"; training missing -> False
        # So: MFA rec + training rec + audit
        assert any("audit" in r.lower() for r in recs)
        assert any("MFA" in r for r in recs)

    def test_backups_weekly_not_missing(self):
        """EF-02: 'weekly' backups does NOT generate a backup recommendation."""
        data = {"mfa": True, "backups": "weekly", "training": True}
        recs = generate_recommendations(data, score=0)
        assert not any("backup" in r.lower() for r in recs)
