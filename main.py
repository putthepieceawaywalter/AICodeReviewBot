from fastapi import FastAPI, Request, Header, HTTPException
import hmac, hashlib
import httpx
import os

app = FastAPI()
GITHUB_SECRET = os.getenv("GITHUB_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
#openai.api_key = 

@app.post("/webhook")
async def github_webhook(request: Request, x_github_event: str = Header(None)):
    body = await request.body()
    payload = await request.json()

    if (1==0):
        raise Exception("1 is not 0")

    if not verify_signature(GITHUB_SECRET, body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event != "pull_request":
        return {"msg": "Not a pull_request event"}


    pr = payload.get("pull_request")
    if not pr:
        raise HTTPException(status_code=400, detail="No pull_request in payload")

    diff_url = pr.get("diff_url")
    comments_url = pr.get("comments_url")
    if not diff_url:
        raise HTTPException(status_code=400, detail="No diff_url in pull_request")

    action = payload.get("action")
    if action not in ["opened", "reopened", "synchronize"]:
        return {"msg": f"Action '{action}' not handled"}
    
    diff_text = await get_pr_diff(diff_url)
    review = await get_ai_review(diff_text)

    comment_body = f"🤖 **AI Code Review Bot says:**\n\n{review}"
    await post_pr_comment(comments_url, comment_body)

    return {"status": "review posted"}

async def post_pr_comment(comments_url: str, message: str):
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(comments_url, headers=headers, json={"body": message})
        response.raise_for_status()

async def get_pr_diff(diff_url: str) -> str:
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    async with httpx.AsyncClient() as client:
        response = await client.get(diff_url, headers=headers)
        response.raise_for_status()
        return response.text

async def get_ai_review(diff_text: str) -> str:
    # TODO : Implement OpenAI API call to analyze the diff_text

    prompt = f"""
You are an expert code reviewer. Here is a Git diff from a pull request:

{diff_text}

Please review this code change for bugs, security issues, performance problems, bad practices, and TODOs. Provide a concise summary with 1-3 actionable points.
"""
    response = await openai.ChatCompletion.acreate(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def verify_signature(secret, body, signature):
    if not signature:
        return False
    hash = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={hash}", signature)

