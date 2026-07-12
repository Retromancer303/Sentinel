import os
import unittest
from urllib.error import URLError
from unittest.mock import patch

from app.services.ai_agent import build_fallback_reply, build_prompt, get_ai_reply


class TestAiAgent(unittest.TestCase):
    def test_fallback_reply_uses_keywords(self):
        reply = build_fallback_reply("How do I reduce phishing risk?")
        self.assertIn("phishing", reply.lower())

    def test_get_ai_reply_falls_back_when_no_provider_configured(self):
        with patch.dict(os.environ, {}, clear=True):
            reply = get_ai_reply("How do I reduce phishing risk?")
            self.assertIn("phishing", reply.lower())

    def test_get_ai_reply_falls_back_when_ollama_is_unavailable(self):
        with patch.dict(os.environ, {"AI_PROVIDER": "ollama"}, clear=True):
            with patch("app.services.ai_agent.request.urlopen", side_effect=URLError("offline")):
                reply = get_ai_reply("How do I reduce phishing risk?")
                self.assertIn("phishing", reply.lower())

    def test_fallback_reply_answers_unknown_prompt_directly(self):
        reply = build_fallback_reply("How do I secure a home network?")
        self.assertIn("home network", reply.lower())

    def test_build_prompt_includes_recent_history(self):
        history = [
            {"role": "user", "content": "What is phishing?"},
            {"role": "assistant", "content": "Phishing is a scam that tricks people into sharing information."},
        ]
        prompt = build_prompt("How can I reduce it?", history)
        self.assertIn("What is phishing?", prompt)
        self.assertIn("How can I reduce it?", prompt)


if __name__ == "__main__":
    unittest.main()
