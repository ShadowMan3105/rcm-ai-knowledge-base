# READ_PROTOCOL.md — How any AI should consume this KB

**Companion to `AI_PROTOCOL.md`.** That file governs *writing*; this one governs *reading*.

If you are an AI (Claude, GPT, Codex, Gemini, Ollama, custom agent…) about to help with anything RCM-, billing-, automation-, or healthcare-operations-related, read [`AGENTS.md`](AGENTS.md) first and then follow these steps **before** generating advice or code.

---

## TL;DR — the one-paragraph version

> Fetch [`index.json`](https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/index.json). Filter entries by tags/domain matching the task. Prefer `status: active`. For each top match, fetch its `report.md` and `lessons.md`. Use that knowledge in your answer. Cite the entry `id` you used. If you find something wrong, do not edit — open a challenge per `AI_PROTOCOL.md` §4.

---

## Canonical URLs

```
INDEX:     https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/index.json
PROTOCOL:  https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/AI_PROTOCOL.md
README:    https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/README.md
GRAPH:     https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/_graph/GRAPH_REPORT.md
GRAPH JSON:https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/_graph/graph.json
GRAPH INC: https://raw.githubusercontent.com/ShadowMan3105/rcm-ai-knowledge-base/main/_graph/incremental-latest/GRAPH_REPORT.md

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

<!-- GRAPHIFY-KB-LAYER:START -->
## Optional Graphify navigation
Graphify may be used after the normal read protocol. It is a navigation aid only.
The cloud-readable graph lives in `_graph/` and is generated locally by the
versioned runner in `ops/graphify/`. The active production path uses
Claude/Sonnet through LiteLLM; Ollama/qwen is fallback/local test infrastructure.

Required behavior:

1. Read `AGENTS.md`, `AI_PROTOCOL.md`, `READ_PROTOCOL.md`, and `index.json` first.
2. If `_graph/GRAPH_REPORT.md` exists, read it as an advisory map.
3. If the task involves recently changed files, read `_graph/incremental-latest/GRAPH_REPORT.md` as the recent-change map.
4. Use `_graph/graph.json`, `_graph/incremental-latest/graph.json`, or Graphify queries to discover candidate relationships, clusters, or paths.
5. Verify every conclusion against the original `meta.json`, `report.md`, `lessons.md`, `challenges/`, and `patches/` files.
6. Treat `EXTRACTED`, `INFERRED`, and `AMBIGUOUS` graph relationships according to their confidence; inferred or ambiguous relationships are not KB truth.
7. Convert substantive findings into a challenge, patch, or new KB entry instead of directly rewriting active content.

See `_schema/graphify-agent-prompt.md` for a copy-paste agent prompt.
<!-- GRAPHIFY-KB-LAYER:END -->
