import os
import unittest
from urllib.error import URLError
from unittest.mock import patch

from app.services.ai_agent import build_fallback_reply, get_ai_reply


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


if __name__ == "__main__":
    unittest.main()
