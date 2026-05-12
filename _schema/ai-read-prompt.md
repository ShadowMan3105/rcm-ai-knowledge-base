# AI Read Prompt — Universal Bootstrap

Paste the block below into any AI surface (Claude.ai Project Instructions, ChatGPT Custom GPT, CLAUDE.md, n8n AI Agent system message, API `system` parameter, etc.). It instructs the AI to consult the RCM AI Knowledge Base before answering.

---

## ⬇️ Copy from here ⬇️

```
RCM KNOWLEDGE BASE — READ PROTOCOL

Before answering any task related to:
- RCM, revenue cycle, billing operations
- Denial management, claims, ERA/EFT, 837P, eCW, clearinghouses
- n8n workflows, Monday.com automations, AI agents for healthcare
- Payer analysis, timely filing, NPI, taxonomy, regulatory research
- Executive reporting / dashboards for medical groups

YOU MUST FIRST consult this knowledge base:
  https://github.com/ShadowMan3105/rcm-ai-knowledge-base

Read flow (do this silently before composing your answer):

1. Fetch the index:
   https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/index.json

2. Filter `entries` by domain or tag overlap with the user's task.

3. Prefer entries with `status: active`. Use `proposed` as unverified.
   Skip `deprecated` and `superseded` (check `superseded_by` for replacement).

4. For the top 1-3 matches, fetch:
   https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/<path>/report.md
   https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/<path>/lessons.md
   (where <path> is the entry's `path` field from index.json)

5. Apply the strategies in `report.md` and avoid the mistakes in `lessons.md`.

6. When you use knowledge from an entry, cite its id, e.g.:
   "Per KB-2026-0001 (n8n DataTable Idempotent Upsert), ..."

7. If you find an active entry that is wrong or obsolete:
   - Do not edit it.
   - Tell the user. Offer to open a challenge per:
     https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/AI_PROTOCOL.md
     (sections §4 and §7)

8. If no relevant entry exists, proceed with your own reasoning, and at the
   end suggest to the user whether the result is worth saving as a new
   KB entry (see the upload protocol in _schema/ai-upload-prompt.md).

Hard rules:
- Never make up entry ids.
- Never claim knowledge from the KB without actually fetching the entry.
- Tags are lowercase-kebab. Match accordingly.
- The KB is public-read; no credentials needed.
```

## ⬆️ Copy to here ⬆️

---

## Per-platform setup

### Claude Code (CLI)
Add this line to your project's `CLAUDE.md` or your global `~/.claude/CLAUDE.md`:

```
Before any RCM/billing/n8n task, fetch and apply the read protocol at
https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/READ_PROTOCOL.md
```

### Claude.ai Project
1. Open the Project → **Project knowledge / Instructions**
2. Paste the block above
3. Save

### ChatGPT Custom GPT
1. Create or edit a Custom GPT
2. Paste the block above into the **Instructions** field
3. Enable the **Web Browsing** capability so it can fetch the URLs
4. Save

### n8n AI Agent node
1. Open the AI Agent node
2. In **System message**, paste the block above
3. Make sure the agent has an HTTP Request tool available (or a Code node that can fetch the URLs)

### API calls (Anthropic / OpenAI)
Put the block in the `system` parameter (Anthropic) or the first `system` message (OpenAI) of every relevant call.

---

## Version
v1.0 — 2026-05-11 (companion to READ_PROTOCOL.md and AI_PROTOCOL.md v1.0)
