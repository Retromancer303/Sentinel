# Sentinel

Sentinel is a local-first cybersecurity assistant and risk dashboard. It combines a lightweight frontend, a FastAPI backend, and a local Ollama-based chatbot so you can ask cybersecurity questions without sending data to a remote service.

## Quick start

```bash
# 1. Clone the repo
git clone <repo-url>
cd Sentinel

# 2. Run the launcher
# Windows: double-click start_sentinel.cmd
# macOS/Linux: ./start_sentinel.sh

# The launcher handles everything else — venv, dependencies, backend, and browser.
```

## Requirements

The launcher script handles setup automatically, but you need these installed first:

| Tool | Required | Notes |
|---|---|---|
| Python 3.10+ | Yes | [python.org](https://www.python.org/downloads/) |
| Ollama | Yes (for AI chat) | [ollama.com](https://ollama.com/) |
| A browser | Yes | Chrome, Edge, Firefox, etc. |
| Redis | No | Optional — for persistent chat history across restarts |

## Setup (if you prefer to do it manually)

### 1. Install Ollama and pull the model

```bash
# Install from https://ollama.com, then:
ollama pull llama3:latest
```

### 2. Create the virtual environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

**Windows:**
```powershell
pip install -r risk-engine\requirements.txt
```

**macOS / Linux:**
```bash
pip install -r risk-engine/requirements.txt
```

### 4. Start the backend

```bash
cd risk-engine
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Open the frontend

Open `frontend/index.html` in your browser, or navigate to the Chat page directly at `frontend/pages/chat.html`.

## How the app works

- **Frontend:** Plain HTML/CSS/JS in the `frontend/` folder. Talks to the backend API.
- **Backend:** FastAPI app in `risk-engine/app/`. Endpoints at `http://127.0.0.1:8000`.
- **Database:** SQLite by default (no setup needed). Override with `DATABASE_URL` env var for PostgreSQL.
- **Chat model:** Ollama by default with `llama3:latest`. Also supports OpenAI and Anthropic via env vars.
- **Chat memory:** The backend stores recent turns per session. Falls back from Redis → SQLite → in-memory.

## Configuration

Set these environment variables to change defaults:

| Variable | Default | Purpose |
|---|---|---|
| `AI_PROVIDER` | `ollama` | `ollama`, `openai`, or `anthropic` |
| `OLLAMA_MODEL` | `llama3:latest` | Model name for Ollama |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OPENAI_API_KEY` | — | Required for OpenAI provider |
| `ANTHROPIC_API_KEY` | — | Required for Anthropic provider |
| `DATABASE_URL` | `sqlite:///./sentinel.db` | Database connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection (optional) |

## Troubleshooting

If the chat returns generic keyword-based replies:

- Confirm Ollama is running: `ollama list`
- Confirm the backend is up: `curl http://127.0.0.1:8000/`
- Check the provider config: `AI_PROVIDER=ollama`, `OLLAMA_HOST=http://127.0.0.1:11434`

## Useful commands

```bash
# Start backend manually
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test the chat endpoint
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","session_id":"demo"}'

# Run tests
python -m unittest discover tests/ -v
```


