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
            "Treat the conversation history as active context. "
            "If the user asks to expand, clarify, elaborate, or continue, answer directly using the earlier topic. "
            "Do not ask them to repeat themselves unless the context is truly missing. "
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
        return "Phishing is a social engineering attack that tricks people into sharing credentials or data. The main defenses are training, email filtering, MFA, and safe reporting habits."
    if "password" in text:
        return "Passwords should be long, unique, and stored in a password manager. MFA should be enabled wherever possible."
    if "mfa" in text:
        return "MFA adds a second verification step and is one of the most effective defenses against account compromise."
    if "backup" in text:
        return "Backups should be tested regularly, encrypted, and kept separate from the main production systems."
    if "ransomware" in text:
        return "Ransomware defense focuses on patching, endpoint protection, least privilege, and tested backups."
    if "home network" in text or "network" in text:
        return "A home network should use a strong Wi-Fi password, updated router firmware, WPA3 if available, and patched devices."
    return "I’m here to help with cybersecurity questions. Please ask about a specific topic such as phishing, passwords, backups, or ransomware."


def get_ai_reply(message: str, history: Optional[list[dict]] = None) -> str:
    os.environ.setdefault("AI_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_MODEL", "llama3:latest")
    os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")

    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    if provider not in {"ollama", "openai", "anthropic"}:
        provider = "ollama"

    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3:latest")
        hosts = []
        configured_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
        if configured_host:
            hosts.append(configured_host)
        if configured_host != "http://127.0.0.1:11434":
            hosts.append("http://127.0.0.1:11434")
        if configured_host != "http://localhost:11434":
            hosts.append("http://localhost:11434")

        for host in hosts:
            for attempt in range(2):
                try:
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
                    with request.urlopen(req, timeout=60) as response:
                        data = json.loads(response.read().decode("utf-8"))
                        text = data.get("response", "").strip()
                        if text:
                            return text
                except (error.URLError, error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError, ssl.SSLError, OSError):
                    if attempt == 0:
                        continue
                    break

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
