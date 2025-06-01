# AI Code Review Bot

This project is an AI-powered GitHub Pull Request review bot that automatically comments on PRs with code quality, bug, and security feedback using OpenAI's GPT models.

---

### To test this bot 
1. Make a branch in this repo
2. Clone the repo
3. Make a change in your branch (include bad code, such as a TODO, variable that doesn't get used, a condition that is unreachable, etc...)
4. Push your changes
5. Create a pull request
6. The bot will automatically comment on the PR with feedback based on the changes made.


## 🚀 Deployment Guide

Follow these steps to deploy the bot and connect it to your GitHub repository.

### 1. Fork or Clone the Repo

```bash
git clone https://github.com/yourusername/aicodereviewbot.git
cd aicodereviewbot
# or fork the repo on GitHub and clone your fork
```
### 2. Create GitHub Personal Access Token
Go to GitHub Tokens. Generate a new token with scopes: 'repo'
Copy the token, you'll need it shortly.

### 3. Create a GitHub Webhook Secret
```bash 
openssl rand -hex 32
```

### 4. Configure Github Webhook
Go to your repository settings, then "Webhooks" and add a new webhook:
- **Payload URL**: `https://yourdomain.com/webhook`
- **Content type**: `application/json`
- **Secret**: Paste the secret you generated in step 3
- **Events**: Select "Let me select individual events" and check "Pull requests"
- **Active**: Ensure this is checked
Save the webhook

### 5. Choose how to deploy
I used fly.io for my deployment, but you can use any platform that supports Node.js applications.

Verify you have the `flyctl` CLI installed. If not, follow the [Fly.io installation guide](https://fly.io/docs/getting-started/installing-flyctl/).
```bash
flyctl launch --name your-app-name --no-deploy
```
### 6. Set Secrets on Fly.io
flyctl secrets set \
  GITHUB_TOKEN=your_github_pat_here \
  GITHUB_WEBHOOK_SECRET=your_webhook_secret_here \
  OPENAI_API_KEY=your_openai_api_key_here

### 7.Deploy the app
```bash
flyctl deploy
```

### 8. Test the Bot
Create a new pull request in your repository. The bot should automatically view the diff and provide feedback. 






