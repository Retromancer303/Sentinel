# Sentinel

Sentinel is a local-first cybersecurity assistant and risk dashboard. It combines a lightweight frontend, a FastAPI backend, and a local Ollama-based chatbot so you can ask cybersecurity questions without sending data to a remote service.

## Apps needed

Before starting Sentinel, make sure these are available on your machine:

- Python 3.10+ (the project uses a local virtual environment)
  - https://www.python.org/downloads/
- Ollama installed and running locally
  - https://ollama.com/
- A local Ollama model available, preferably:
  - llama3:latest
  - Install it with: ollama pull llama3:latest
- Redis (optional for chat history persistence, but the app can still run without it)
  - https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/
- Docker Desktop (optional, useful if you want to run Redis in a container)
  - https://www.docker.com/products/docker-desktop/
- A browser such as Chrome or Edge

## Install and prepare the project

Follow these steps in order on a Windows machine.

### 1. Open the project folder
Open a terminal in the project root:
- <your-project-folder>\Sentinel

### 2. Create a Python virtual environment
If you do not already have one, create a local virtual environment:
- python -m venv .venv

Activate it in PowerShell:
- .\.venv\Scripts\Activate.ps1

If PowerShell blocks the activation script, run this once in the current terminal:
- Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned

### 3. Install Python dependencies
From the project root, install the backend requirements:
- pip install -r risk-engine\requirements.txt
- pip install sqlalchemy psycopg2-binary redis

These packages are needed for:
- FastAPI and Uvicorn for the backend API
- SQLAlchemy for database access
- psycopg2-binary for PostgreSQL connectivity
- redis for chat history storage

### 4. Install and start Ollama
Install Ollama from https://ollama.com/ and make sure the service is running.

After installation, open a terminal and confirm Ollama is available:
- ollama --version

Pull the model used by Sentinel:
- ollama pull llama3:latest

You can verify the model is available with:
- ollama list

### 5. Optional: start Redis
Redis is used for chat history persistence. If you want that feature enabled, you can start Redis either locally or with Docker Desktop.

#### Option A: start Redis locally
If you have Redis installed on your machine:
- redis-server

#### Option B: start Redis with Docker Desktop
If you are using Docker Desktop, you can run Redis in a container:
- docker pull redis:latest
- docker run --name sentinel-redis -p 6379:6379 -d redis:latest

To verify that Redis is running:
- docker ps
- docker logs sentinel-redis

You can also test it from PowerShell:
- redis-cli ping

If Redis is not running, Sentinel can still start, but chat history may fall back to in-memory storage.

### 6. Verify the environment before launching
Before starting the app, confirm the following:
- The virtual environment is active
- Ollama is running
- The llama3:latest model is installed
- The backend can reach the local Ollama server on http://127.0.0.1:11434

You can test the Ollama API with:
- curl http://127.0.0.1:11434/api/tags

If you are using PowerShell, this is also fine:
- Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags

## Start the app

You can launch Sentinel by double-clicking one of these files from the project folder:

- start_sentinel.cmd
- start_sentinel.ps1

The launcher will:
- stop any older Sentinel backend processes,
- start the FastAPI backend on port 8000,
- wait until the backend is ready,
- open the frontend in your browser.

## How the app works

- Frontend: the browser UI lives in the frontend folder and talks to the backend API.
- Backend: the FastAPI app is in risk-engine/app.
- Chat model: the chatbot uses Ollama by default with the model llama3:latest.
- Chat memory: the backend stores recent turns per session so the conversation can continue naturally.

## Common issues

If the chat falls back to the generic response:

- confirm Ollama is running,
- confirm the model exists with:
  - ollama list
- confirm the backend is reachable at:
  - http://127.0.0.1:8000/
- confirm the chatbot service is using the expected environment variables:
  - AI_PROVIDER=ollama
  - OLLAMA_MODEL=llama3:latest
  - OLLAMA_HOST=http://127.0.0.1:11434

## Useful commands

- Start the backend manually:
  - .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
- Test the chat endpoint:
  - Invoke-RestMethod -Uri http://127.0.0.1:8000/chat -Method Post -ContentType application/json -Body '{"message":"Hello","session_id":"demo"}'
