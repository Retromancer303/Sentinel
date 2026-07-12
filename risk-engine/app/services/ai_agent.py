# AI agent — handles communication with LLM providers and generates chat replies.
#
# Supports three providers (controlled by AI_PROVIDER env var):
#   - "ollama"   — local Ollama instance (default, uses urllib)
#   - "openai"   — OpenAI API (requires OPENAI_API_KEY)
#   - "anthropic" — Anthropic API (requires ANTHROPIC_API_KEY)
#
# If no provider is available, falls back to keyword-based static replies.

import json
import os
import ssl
from urllib import error, request

# Shared system prompt used by all providers to set the assistant’s role.
SYSTEM_PROMPT = "You are a friendly cybersecurity assistant for Sentinel."


# ── Prompt builders ──────────────────────────────────────────────────────────


def build_prompt(message: str, history: list[dict] | None = None) -> str:
    """Build a context-aware prompt for Ollama that includes conversation history.

    Ollama’s /api/generate endpoint takes a single prompt string, so we format
    the history as "Role: content" lines and append the current question.
    """
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
            f"{SYSTEM_PROMPT} "
            "Treat the conversation history as active context. "
            "If the user asks to expand, clarify, elaborate, or continue, answer directly using the earlier topic. "
            "Do not ask them to repeat themselves unless the context is truly missing. "
            f"Conversation so far:\n{context_text}\n\n"
            f"Current user question: {message}"
        )

    return (
        f"{SYSTEM_PROMPT} "
        "Answer the user’s question directly and naturally, in 2-4 sentences, "
        f"without repeating generic templates. User question: {message}"
    )


def build_history_messages(history: list[dict] | None = None) -> list[dict]:
    """Convert conversation history into the message format used by OpenAI/Anthropic.

    These APIs expect a list of {"role": "user"|"assistant", "content": "..."} dicts
    rather than a single prompt string.
    """
    messages = []
    for turn in history or []:
        role = turn.get("role", "user")
        content = turn.get("content", "").strip()
        if content:
            messages.append({"role": role, "content": content})
    return messages


def build_fallback_reply(message: str) -> str:
    """Return a static keyword-based reply when no AI provider is available.

    This is the last resort — it ensures the user always gets a response
    even if Ollama, OpenAI, and Anthropic are all unreachable.
    """
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


# ── Provider-specific functions ──────────────────────────────────────────────
# Each function tries to get a reply from one provider and returns None on failure.
# The dispatcher (get_ai_reply) calls them in order and falls back to keywords.


def _try_ollama(message: str, history: list[dict] | None = None) -> str | None:
    """Try to get a reply from a local Ollama instance.

    Tries multiple hosts (configured host, 127.0.0.1, localhost) with 2 attempts
    each. This handles the common case where Ollama is running but the hostname
    resolves differently than expected.
    """
    model = os.getenv("OLLAMA_MODEL", "llama3:latest")
    configured_host = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()

    # Build a list of hosts to try — the configured one plus common alternatives.
    hosts = []
    if configured_host:
        hosts.append(configured_host)
    if configured_host != "http://127.0.0.1:11434":
        hosts.append("http://127.0.0.1:11434")
    if configured_host != "http://localhost:11434":
        hosts.append("http://localhost:11434")

    prompt = build_prompt(message, history)

    # Try each host with up to 2 attempts before moving on.
    for host in hosts:
        for attempt in range(2):
            try:
                payload = {
                    "model": model,
                    "prompt": prompt,
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
            except (error.URLError, error.HTTPError, TimeoutError, ValueError,
                    json.JSONDecodeError, ssl.SSLError, OSError):
                if attempt == 0:
                    continue
                break

    return None


def _try_openai(message: str, history: list[dict] | None = None) -> str | None:
    """Try to get a reply from the OpenAI API. Returns None if unavailable.

    The openai package is imported lazily so the app still works if it’s not installed.
    """
    try:
        import openai
    except ImportError:
        return None

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = openai.OpenAI(api_key=api_key)

    # Build the message list: system prompt + conversation history + current question.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(build_history_messages(history))
    messages.append({"role": "user", "content": message})

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        input=messages,
    )
    return response.output_text.strip() or None


def _try_anthropic(message: str, history: list[dict] | None = None) -> str | None:
    """Try to get a reply from the Anthropic API. Returns None if unavailable.

    The anthropic package is imported lazily so the app still works if it’s not installed.
    """
    try:
        import anthropic
    except ImportError:
        return None

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    client = anthropic.Anthropic(api_key=api_key)

    # Anthropic uses a separate "system" parameter instead of a system message.
    messages = build_history_messages(history)
    messages.append({"role": "user", "content": message})

    response = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text.strip() or None


# ── Main dispatcher ──────────────────────────────────────────────────────────


def get_ai_reply(message: str, history: list[dict] | None = None) -> str:
    """Return an AI-generated reply to the user’s cybersecurity question.

    Provider selection is controlled by the AI_PROVIDER environment variable:
    - "ollama" (default): Calls a local Ollama instance.
    - "openai": Uses the OpenAI API. Requires OPENAI_API_KEY.
    - "anthropic": Uses the Anthropic API. Requires ANTHROPIC_API_KEY.

    Falls back to keyword-based static replies if the provider is unavailable.
    """
    # Set sensible defaults so the app works out of the box with Ollama.
    os.environ.setdefault("AI_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_MODEL", "llama3:latest")
    os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")

    provider = os.getenv("AI_PROVIDER", "ollama").strip().lower()
    if provider not in {"ollama", "openai", "anthropic"}:
        provider = "ollama"

    reply = None

    if provider == "ollama":
        reply = _try_ollama(message, history)
    elif provider == "openai":
        reply = _try_openai(message, history)
    elif provider == "anthropic":
        reply = _try_anthropic(message, history)

    # If the provider failed or returned nothing, use the keyword fallback.
    return reply or build_fallback_reply(message)
