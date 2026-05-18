from fastapi import FastAPI
from app.api.risk_routes import router

app = FastAPI()

app.include_router(router)

@app.get("/")
def home():
    return {"status": "Risk engine running"}