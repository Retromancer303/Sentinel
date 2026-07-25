"""
Unit tests for AI agent fallback replies and prompt builders.
"""
import os
from urllib.error import URLError
from unittest.mock import patch

import pytest
from app.services.ai_agent import (
    build_fallback_reply,
    build_history_messages,
    build_prompt,
    get_ai_reply,
)


class TestAiAgentFallback:
    """UC-CHAT-02: AI fallback when no provider is available."""

    # ── Normal Flows ──────────────────────────────────────────────────────

    def test_fallback_phishing_keyword(self):
        """NF-01: 'phishing' keyword returns phishing-specific guidance."""
        reply = build_fallback_reply("How do I reduce phishing risk?")
        assert "phishing" in reply.lower()
        assert "MFA" in reply

    def test_fallback_password_keyword(self):
        """NF-02: 'password' keyword returns password security guidance."""
        reply = build_fallback_reply("How to create strong passwords?")
        assert "password" in reply.lower()

    def test_fallback_mfa_keyword(self):
        """NF-03: 'mfa' keyword returns MFA guidance."""
        reply = build_fallback_reply("Should I enable MFA?")
        assert "MFA" in reply

    def test_fallback_backup_keyword(self):
        """NF-04: 'backup' keyword returns backup guidance."""
        reply = build_fallback_reply("How often should I backup?")
        assert "backup" in reply.lower()

    def test_fallback_ransomware_keyword(self):
        """NF-05: 'ransomware' keyword returns ransomware defense guidance."""
        reply = build_fallback_reply("How to defend against ransomware?")
        assert "ransomware" in reply.lower()

    def test_fallback_network_keyword(self):
        """NF-06: 'network' keyword returns network security guidance."""
        reply = build_fallback_reply("How do I secure my home network?")
        assert "network" in reply.lower()
        assert "WPA3" in reply

    # ── Alternate Flows ───────────────────────────────────────────────────

    def test_fallback_case_insensitive(self):
        """AF-01: Keyword matching is case-insensitive."""
        reply = build_fallback_reply("What is PHISHING?")
        assert "phishing" in reply.lower()

    def test_fallback_unknown_topic(self):
        """AF-02: Unknown topic returns a generic prompt to ask about known topics."""
        reply = build_fallback_reply("Tell me about quantum computing")
        assert "phishing" in reply.lower()
        assert "passwords" in reply.lower()

    # ── Exceptional Flows ─────────────────────────────────────────────────

    def test_fallback_empty_string(self):
        """EF-01: Empty string returns the generic fallback."""
        reply = build_fallback_reply("")
        assert "Ask me about" in reply

    def test_get_ai_reply_falls_back_with_empty_env(self):
        """EF-02: Cleared environment causes fallback to keyword replies."""
        with patch.dict(os.environ, {}, clear=True):
            reply = get_ai_reply("How do I reduce phishing risk?")
            assert "phishing" in reply.lower()

    def test_get_ai_reply_falls_back_when_ollama_offline(self):
        """EF-03: When Ollama is unreachable, falls back to keyword replies."""
        with patch.dict(os.environ, {"AI_PROVIDER": "ollama"}, clear=True):
            with patch("app.services.ai_agent.request.urlopen", side_effect=URLError("offline")):
                reply = get_ai_reply("What is ransomware?")
                assert "ransomware" in reply.lower()


class TestPromptBuilder:
    """UC-CHAT-03: Prompt construction for AI providers."""

    def test_build_prompt_includes_history(self):
        """NF-01: Prompt includes conversation history for context."""
        history = [
            {"role": "user", "content": "What is phishing?"},
            {"role": "assistant", "content": "Phishing is a scam."},
        ]
        prompt = build_prompt("How can I reduce it?", history)
        assert "What is phishing?" in prompt
        assert "How can I reduce it?" in prompt
        assert "Conversation so far" in prompt

    def test_build_prompt_no_history(self):
        """NF-02: Prompt without history doesn't include conversation section."""
        prompt = build_prompt("What is MFA?", history=None)
        assert "Conversation so far" not in prompt
        assert "What is MFA?" in prompt

    def test_build_prompt_empty_history(self):
        """NF-03: Empty history list handled same as None."""
        prompt = build_prompt("Hello", history=[])
        assert "Conversation so far" not in prompt

    def test_build_prompt_skips_empty_content(self):
        """AF-01: History entries with empty content are skipped."""
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Real reply"},
        ]
        prompt = build_prompt("Question?", history)
        # The empty user message should not appear; only the assistant's reply
        assert "Real reply" in prompt
        assert "User:" not in prompt  # No user line since content was empty

    def test_build_history_messages_converts_format(self):
        """NF-04: History messages are converted to OpenAI/Anthropic format."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        messages = build_history_messages(history)
        assert len(messages) == 2
        assert messages[0] == {"role": "user", "content": "Hello"}
        assert messages[1] == {"role": "assistant", "content": "Hi there"}

    def test_build_history_messages_empty_input(self):
        """AF-02: None or empty input returns empty list."""
        assert build_history_messages(None) == []
        assert build_history_messages([]) == []
