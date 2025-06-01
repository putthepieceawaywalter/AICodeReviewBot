from fastapi import FastAPI, Request, Header, HTTPException
import hmac, hashlib
import httpx
import os
from openai import AsyncOpenAI
import base64
import json

app = FastAPI()


# Load environment variables, these are set using flyctl secrets set commands
GITHUB_SECRET = os.getenv("GITHUB_SECRET", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = AsyncOpenAI()
repo_name = "putthepieceawaywalter/AICodeReviewBot"

@app.post("/webhook")
async def github_webhook(
        request: Request, 
        x_hub_signature_256: str = Header(None, convert_underscores=False), 
        x_github_event: str = Header(None),
        ):

    if not GITHUB_SECRET or not GITHUB_TOKEN or not OPENAI_API_KEY:
        raise RuntimeError("Missing required environment variables.")

    body = await request.body()
    payload = await request.json()

    if (1==0):
        raise Exception("1 is not 0")

    if x_github_event != "pull_request":
        return {"msg": "Not a pull_request event"}

    pr = payload.get("pull_request")
    if not pr:
        raise HTTPException(status_code=400, detail="No pull_request in payload")

    diff_url = pr.get("diff_url")
    comments_url = pr.get("comments_url")
    if not diff_url:
        raise HTTPException(status_code=400, detail="No diff_url in pull_request")

    if not comments_url:
        raise HTTPException(status_code=400, detail="No comments_url in pull_request")

    action = payload.get("action")
    if action not in ["opened", "reopened", "synchronize"]:
        return {"msg": f"Action '{action}' not handled"}
    
    diff_text = await get_pr_diff(diff_url)
    if not diff_text:
        raise HTTPException(status_code=400, detail="No diff text found")
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
        response = await client.get(diff_url, headers=headers, follow_redirects=True)
        response.raise_for_status()
        return response.text

async def get_ai_review(diff_text: str) -> str:
    # no error checking for config here because it will still succeed without it
    # another branch will implement logging, which will document when and why the config isn't being pulled
    config = await fetch_reviewbot_config(repo_name)

    prompt_prefix = config.get("prompt_prefix", "")
    focus_areas = ", ".join(config.get("focus_areas", ["bugs", "security", "TODOs", "performance", "dead code"]))

    prompt = f"""
    {prompt_prefix}

    You are a strict expert code reviewer.

    Below is a Git diff from a pull request:

    {diff_text}

    Your job is to identify any of the following issues, be sure to include which function the issue is in:
    - Bugs or incorrect logic
    - Security vulnerabilities
    - Performance problems
    - Bad or unidiomatic code practices
    - Presence of TODOs
    - Dead code or unreachable conditions
    - Missing error handling
    

    Instructions:
    - Be concise, direct, and use bullet points.
    - Organize your feedback by the file name, each file is a bullet point with sub bullets indicating line number and issue.
    - Only comment on issues or concerns; don't summarize the code.
    - If no issues are found, say: "No issues found."

    Begin your review now:
    """
    response = await client.chat.completions.create(
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


async def fetch_reviewbot_config(repo_full_name: str, branch: str = "main") -> dict:
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/reviewbot.json?ref={branch}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
        else:
            print(f"Config not found or failed to load: {response.status_code}")
            # printing the error for now, another branch will implement logging
            return {}

