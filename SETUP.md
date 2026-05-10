# GitHub Setup Instructions

## Step 1 — Create the Repo (you do this, 2 minutes)

1. Go to https://github.com/new
2. Name: `rcm-ai-knowledge-base` (or your preference)
3. Visibility: **Public**
4. Do NOT initialize with README (we have one)
5. Click **Create repository**

---

## Step 2 — Create a Personal Access Token (PAT)

This is the credential AI agents will use to push entries.

1. GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Name: `kb-writer`
4. Expiration: No expiration (or 1 year — your call)
5. Scopes: check only `repo` (full control of private/public repos)
6. Click **Generate token**
7. **Copy it immediately** — GitHub won't show it again
8. Store it in your password manager

This token is what you give to Claude (or any AI) when approving an upload.

---

## Step 3 — Push Initial Structure (Claude does this with your PAT)

Once you have the PAT and repo URL, tell Claude:
> "Push the KB structure to GitHub. Repo: [your-username]/rcm-ai-knowledge-base. PAT: [your-token]"

Claude will run the git commands to initialize and push.

---

## Step 4 — Add Upload Prompt to Claude Projects

1. In Claude.ai, open or create a Project for RCM work
2. Go to Project Instructions
3. Paste the content from `_schema/ai-upload-prompt.md`
4. Save

From that point forward, every successful session will end with the upload offer.

---

## Notes
- PAT gives write access — only share with trusted AI sessions
- You can revoke and regenerate the PAT anytime from GitHub settings
- Repo is public: anyone can read, only PAT holders can write
