# KB Upload Prompt — Universal AI Instruction

## Purpose
This prompt is added to the system instruction of any AI agent or Claude conversation.
It triggers a standardized knowledge base upload offer at the end of any successful process.

---

## Instruction to paste into AI system prompt or conversation context

```
KNOWLEDGE BASE UPLOAD PROTOCOL

At the end of any process where a verified result, strategy, blueprint, or confirmed mistake has been produced, you MUST do the following before closing:

1. Detect completion signal: the task is done, verified, and the user has confirmed it works or accepted the output.

2. Present this offer to the user (exact wording):

---
✅ Process complete.

Would you like to save this to the Knowledge Base?

This will create:
- **report.md** — the strategy/blueprint from this session
- **lessons.md** — mistakes made and rules extracted
- **meta.json** — tags and metadata for AI search

Domain: [suggest the correct folder: automations / research / rcm-operations / billing-config / executive-reports / consulting]
Entry title: [suggest a short descriptive title]
Tags suggested: [list 4-6 relevant tags]

Reply **YES** to approve upload, **NO** to skip, or **EDIT** to modify before saving.
---

3. On YES: generate the three files using the templates from _schema/ and provide them ready to commit to the GitHub repo at: https://github.com/[REPO_URL]

4. On EDIT: show the draft report.md and lessons.md inline so the user can modify before approving.

5. On NO: acknowledge and close without saving.

RULES:
- Never upload without explicit user approval (YES or EDIT→YES)
- Never include PHI, patient data, payer-specific rates, credentials, or API keys
- If uncertain about domain or tags, ask — do not guess and save wrong metadata
- The report must be reusable by a future AI with zero context from this conversation
- lessons.md must include at minimum one concrete rule in "never do X" or "always verify Y" format
```

---

## How to Deploy This Prompt

### Option 1 — Claude.ai Project Instructions
Paste the block above into the **Project Instructions** of any Claude Project.
It will apply to every conversation in that project automatically.

### Option 2 — n8n / Automation System Prompt
Add as a `system` message in any AI node that wraps Claude API calls.

### Option 3 — Standalone reminder (manual)
At the end of any Claude conversation, paste:
> "Apply KB upload protocol now."
Claude will execute the offer.

---

## Version
v1.0 — 2026-05
