import json
import os
import ssl
from typing import Optional
from urllib import error, request


def build_fallback_reply(message: str) -> str:
    text = message.lower()
    if "phishing" in text:
        return "Phishing risk is reduced with employee training, email filtering, MFA, and a clear reporting process."
    if "password" in text:
        return "Password risk is reduced with long unique passwords, a password manager, MFA, and removing shared accounts."
    if "mfa" in text:
        return "Multi-factor authentication should be enabled for email, VPN, admin panels, cloud services, and financial systems."
    if "backup" in text:
        return "Backups should be encrypted, tested regularly, and stored separately from production systems."
    if "ransomware" in text:
        return "Ransomware defenses include tested backups, patching, endpoint protection, least privilege, and user awareness training."
    return (
        "I can help with cybersecurity risk questions. Ask about phishing, MFA, passwords, backups, ransomware, firewalls, patching, or risk scoring."
    )


def get_ai_reply(message: str) -> str:
    provider = os.getenv("AI_PROVIDER", "ollama").lower()

    if provider == "ollama":
        try:
            model = os.getenv("OLLAMA_MODEL", "llama3")
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            payload = {
                "model": model,
                "prompt": message,
                "stream": False,
            }
            req = request.Request(
                f"{host}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                text = data.get("response", "").strip()
                return text or build_fallback_reply(message)
        except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError, ssl.SSLError, OSError):
            return build_fallback_reply(message)

    if provider == "openai":
        try:
            import openai
        except ImportError:
            return build_fallback_reply(message)

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return build_fallback_reply(message)

        client = openai.OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            input=[{"role": "system", "content": "You are a cybersecurity risk assistant for Sentinel."}, {"role": "user", "content": message}],
        )
        return response.output_text.strip() or build_fallback_reply(message)

    if provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            return build_fallback_reply(message)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return build_fallback_reply(message)

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            max_tokens=300,
            system="You are a cybersecurity risk assistant for Sentinel.",
            messages=[{"role": "user", "content": message}],
        )
        return response.content[0].text.strip() or build_fallback_reply(message)

    return build_fallback_reply(message)
