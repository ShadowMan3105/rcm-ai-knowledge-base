# GitHub Setup Instructions

## Step 1 — Create the Repo (you do this, 2 minutes)

1. Go to https://github.com/new
2. Name: `rcm-ai-knowledge-base` (or your preference)
3. Visibility: **Public**
4. Do NOT initialize with README (we have one)
5. Click **Create repository**

---

## Step 2 — Configure GitHub authentication securely

Use local GitHub authentication through GitHub CLI browser login or your operating-system credential manager.

Do not paste GitHub credentials into chat, repository files, shell history, commits, pull requests, or issue comments.

If a short-lived repo-scoped credential is ever required, keep it local to your machine, store it in a password manager, and rotate it immediately if it is exposed.

---

## Step 3 — Push Initial Structure

After local GitHub authentication is configured, tell the agent:
> "Push the KB structure to GitHub. Repo: [your-username]/rcm-ai-knowledge-base."

The agent should use the local Git credential flow. Do not include secret values in the prompt.

---

## Step 4 — Add Upload Prompt to Claude Projects

1. In Claude.ai, open or create a Project for RCM work
2. Go to Project Instructions
3. Paste the content from `_schema/ai-upload-prompt.md`
4. Save

From that point forward, every successful session will end with the upload offer.

---

## Notes
- Use least-privilege GitHub access.
- Revoke or rotate any credential that appears in chat, logs, commits, or docs.
- Repo is public: anyone can read; only authorized collaborators can write.

<!-- GRAPHIFY-KB-LAYER:START -->
## Optional: Graphify setup

Install Graphify:

```bash
uv tool install graphifyy
# or
pipx install graphifyy
```

Build the curated corpus and run a dry-run:

```bash
python _tools/build_graphify_corpus.py
python _tools/run_graphify_kb.py --dry-run
```

Run extraction with a backend:

```bash
python _tools/run_graphify_kb.py --backend openai --no-viz
python _tools/run_graphify_kb.py --backend gemini --no-viz
OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=llama3.1 python _tools/run_graphify_kb.py --backend ollama --no-viz
```

Set backend credentials only in your local shell environment. Never commit API keys or paste them into repository files.
<!-- GRAPHIFY-KB-LAYER:END -->
