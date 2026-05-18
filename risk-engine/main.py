from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Request(BaseModel):
    message: str

@app.post("/analyze")
def analyze(req: Request):

    msg = req.message.lower()

    risk = 0
    response = ""

    if "mfa" in msg:
        risk += 25
        response = "Enable MFA to reduce account compromise risk."

    elif "phishing" in msg:
        risk += 30
        response = "Train employees to identify phishing emails."

    else:
        response = "I can help assess cybersecurity risks."

    return {
        "response": response,
        "risk_impact": risk
    }