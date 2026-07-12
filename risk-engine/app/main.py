# Application entry point — creates the FastAPI app and configures middleware.
# Run with: uvicorn app.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.risk_routes import router

app = FastAPI()

# CORS allows the frontend (running on a different port) to call this API.
# allow_origins=["*"] is fine for local development but should be restricted in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes from the risk_routes module.
app.include_router(router)


@app.get("/")
def home():
    """Simple health check so you can verify the server is running."""
    return {"status": "Risk engine running"}
