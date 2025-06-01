from fastapi import FastAPI, Request
import hmac, hashlib
import os

app = FastAPI()

GITHUB_SECRET = os.getenv("GITHUB_SECRET", "")

@app.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not verify_signature(GITHUB_SECRET, body, signature):
        return {"error": "Invalid signature"}

    payload = await request.json()
    # TODO: process PR event
    print(payload)
    return {"status": "ok"}

def verify_signature(secret, body, signature):
    if not signature:
        return False
    hash = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={hash}", signature)

