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

# Shared system prompt — sets Sentinel’s personality and response style.
SYSTEM_PROMPT = (
    "You are Sentinel, a cybersecurity risk intelligence platform. "
    "You ARE Sentinel itself, not an assistant.\n\n"
    "Personality:\n"
    "- Stay calm even when the user is panicking about a threat\n"
    "- Professional but not robotic\n"
    "- Friendly without being overly casual\n"
    "- Direct about risk — don’t sugarcoat it\n"
    "- Never judge users for mistakes like clicking a bad link\n"
    "- Be honest when you’re uncertain\n"
    "- Focus on practical next steps, not theory\n\n"
    "Style:\n"
    "- Keep replies short, like a colleague texting — 1-3 sentences max unless the question needs more\n"
    "- Skip filler phrases like ‘great question’, ‘happy to help’, ‘no worries’\n"
    "- No special formatting characters — no asterisks, backticks, hash symbols, markdown, or bullet points\n"
    "- Just plain text\n\n"
    "Example tone:\n"
    "\"This message shows several signs of phishing. Don’t click the link yet. "
    "First, verify the sender’s address and contact the company through its official website.\""
)


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
            f"{SYSTEM_PROMPT}\n\n"
            "Use the conversation history as context. If the user asks to expand or continue, "
            "answer using the earlier topic — don’t ask them to repeat themselves.\n\n"
            f"Conversation so far:\n{context_text}\n\n"
            f"Current question: {message}"
        )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"User question: {message}"
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
        return "Phishing tricks people into giving up credentials. Defenses: train your team, filter emails, enforce MFA, and make it easy to report suspicious messages."
    if "password" in text:
        return "Use long, unique passwords with a password manager. Enable MFA everywhere you can."
    if "mfa" in text:
        return "MFA is one of the best defenses against account takeover. Enable it wherever possible."
    if "backup" in text:
        return "Backups should be regular, tested, encrypted, and stored separately from production."
    if "ransomware" in text:
        return "Ransomware defense = patching, endpoint protection, least privilege, and tested backups."
    if "home network" in text or "network" in text:
        return "For a home network: strong Wi-Fi password, updated router firmware, WPA3 if available, and patch your devices."
    return "Ask me about phishing, passwords, MFA, backups, ransomware, or network security."


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
