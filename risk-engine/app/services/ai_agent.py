import json
import os
import ssl
from typing import Optional
from urllib import error, request


def build_prompt(message: str, history: Optional[list[dict]] = None) -> str:
    history = history or []
    context_parts = []
    for turn in history:
        role = turn.get("role", "user")
        content = turn.get("content", "").strip()
        if content:
            context_parts.append(f"{role.title()}: {content}")

    if context_parts:
        context_text = "\n".join(context_parts)
        return (
            "You are a friendly cybersecurity assistant for Sentinel. "
            "Use the previous conversation to answer naturally. "
            f"Conversation so far:\n{context_text}\n\n"
            f"Current user question: {message}"
        )

    return (
        "You are a friendly cybersecurity assistant for Sentinel. "
        "Answer the user's question directly and naturally, in 2-4 sentences, "
        f"without repeating generic templates. User question: {message}"
    )


def build_fallback_reply(message: str) -> str:
    text = message.lower()
    if "phishing" in text:
        return "Phishing risk is reduced by training staff, filtering suspicious emails, enabling MFA, and creating a clear reporting process."
    if "password" in text:
        return "Password risk is reduced by using long unique passwords, a password manager, MFA, and removing shared accounts."
    if "mfa" in text:
        return "Multi-factor authentication should be enabled for email, VPN, admin panels, cloud services, and financial systems."
    if "backup" in text:
        return "Backups should be encrypted, tested regularly, and stored separately from production systems."
    if "ransomware" in text:
        return "Ransomware defenses include tested backups, patching, endpoint protection, least privilege, and user awareness training."
    if "home network" in text or "network" in text:
        return "For a home network, secure your router, change default passwords, enable WPA3, update firmware, and keep devices patched."
    return (
        f"Absolutely — for a question like this, the best first step is to focus on the main weak spots: use MFA, keep software updated, back up important data, and stay alert to suspicious emails or links. If you want, I can break it down into simple steps for your situation."
    )


def get_ai_reply(message: str, history: Optional[list[dict]] = None) -> str:
    os.environ.setdefault("AI_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_MODEL", "llama3:latest")
    os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")

    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    if provider not in {"ollama", "openai", "anthropic"}:
        provider = "ollama"

    if provider == "ollama":
        try:
            model = os.getenv("OLLAMA_MODEL", "llama3:latest")
            host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            payload = {
                "model": model,
                "prompt": build_prompt(message, history),
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
