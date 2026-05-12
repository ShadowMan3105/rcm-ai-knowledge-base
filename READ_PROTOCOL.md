# READ_PROTOCOL.md — How any AI should consume this KB

**Companion to `AI_PROTOCOL.md`.** That file governs *writing*; this one governs *reading*.

If you are an AI (Claude, GPT, Codex, Gemini, Ollama, custom agent…) about to help with anything RCM-, billing-, automation-, or healthcare-operations-related, follow these steps **before** generating advice or code.

---

## TL;DR — the one-paragraph version

> Fetch [`index.json`](https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/index.json). Filter entries by tags/domain matching the task. Prefer `status: active`. For each top match, fetch its `report.md` and `lessons.md`. Use that knowledge in your answer. Cite the entry `id` you used. If you find something wrong, do not edit — open a challenge per `AI_PROTOCOL.md` §4.

---

## Canonical URLs

```
INDEX:     https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/index.json
PROTOCOL:  https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/AI_PROTOCOL.md
README:    https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/README.md

ENTRY meta:    https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/<path>/meta.json
ENTRY report:  https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/<path>/report.md
ENTRY lessons: https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/<path>/lessons.md
```

`<path>` is the `path` field inside each entry in `index.json`, e.g. `automations/n8n-datatable-idempotent-upsert-pdf-parser/`.

---

## The 6-step read flow

1. **Fetch `index.json`.** Cache it for the session (it is regenerated only on commits).
2. **Detect domain.** Map the user's task to one of: `automations`, `research`, `rcm-operations`, `billing-config`, `executive-reports`, `consulting`.
3. **Filter** `index.json.entries` by:
   - `domain` match (hard filter), OR
   - any overlap between user's keywords and `tags` (soft filter).
4. **Rank** the filtered set:
   - `status: active` first.
   - `status: proposed` next (mark as "unverified" when citing).
   - `status: challenged` → cite cautiously; mention the challenge.
   - `status: deprecated` / `superseded` → do not apply; check `superseded_by` for the replacement.
   - Within the same status, prefer higher `confidence` and more recent `last_verified`.
5. **Fetch the 1-3 top-ranked entries' `report.md` and `lessons.md`** via the URLs above.
6. **Use** that knowledge in your answer. When you do, **cite the entry `id`** so the user can audit (e.g. *"per `KB-2026-0001`, the n8n DataTable node must…"*).

---

## What to do when you spot a problem

If, while reading an `active` entry, you discover it is wrong or obsolete:

- **Do not modify** `report.md` or `lessons.md`.
- Either:
  - Tell the user, and offer to open a challenge per `AI_PROTOCOL.md` §4, **or**
  - If the user authorizes, follow §4 to create `challenges/CH-YYYY-MM-DD-slug.md`.

This way the KB never silently regresses.

---

## Avoiding stale reads

- `index.json` is rebuilt on every commit. Refetch at session start.
- `meta.json`'s `last_verified` tells you how recently a human or curator re-checked the entry. If it is older than your judgment requires for the domain, say so when citing.
- Tags are lowercase-kebab. Don't fuzzy-match too loosely.

---

## Plug-and-play prompt

A ready-to-paste system prompt that triggers the read flow above lives in [`_schema/ai-read-prompt.md`](_schema/ai-read-prompt.md). Paste it into:

- Claude.ai Project Instructions
- ChatGPT Custom GPT system prompt
- A `CLAUDE.md` for Claude Code
- The system message in an Anthropic / OpenAI API call
- An n8n AI Agent's "System message" field

---

## Optional: query the KB from the terminal

```bash
python _tools/query.py --tag n8n --status active
python _tools/query.py --domain automations
python _tools/query.py --search "claims dedupe"
```

See `_tools/query.py --help`.
