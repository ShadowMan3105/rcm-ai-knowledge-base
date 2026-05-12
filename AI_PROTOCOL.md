# AI_PROTOCOL.md — Multi-Agent Contract (v1.0)

**Read this BEFORE writing anything to this repository.**

This file is the contract every AI agent (Claude, GPT, Codex, Gemini, Ollama, etc.) MUST follow when contributing to `rcm-ai-knowledge-base`. The goal is multi-agent safety: any new agent can read, contribute, and challenge prior work without breaking what previous agents established.

---

## 1. Glossary

- **Entry** — a folder under a domain (`automations/`, `research/`, etc.) containing `meta.json`, `report.md`, `lessons.md`, and a `revisions/` subfolder.
- **Domain** — top-level folder grouping related entries.
- **Challenge** — a formal proposal to deprecate or modify an existing `active` entry, stored under `/challenges/`.
- **Revision** — an immutable snapshot of an entry at a point in time, stored under `<entry>/revisions/`.
- **Curator** — the human (Dr. Seidel) who resolves challenges and approves status changes.

---

## 2. Lifecycle of an Entry

```
proposed ──► active ──► challenged ──► (deprecated | superseded)
                  └─────────────────► deprecated  (curator-decided, no challenge needed)
```

| Status | Meaning |
|---|---|
| `proposed` | New entry, not yet verified by the curator. AIs may read, but treat as low-confidence. |
| `active` | Verified and considered correct. Other AIs may reference but **must not edit directly** (see §4). |
| `challenged` | An open challenge exists. Treat findings as uncertain until resolved. |
| `deprecated` | No longer valid. Kept for historical context. Do not apply its guidance. |
| `superseded` | Replaced by a newer entry. The `superseded_by` field points to the replacement. |

---

## 3. Immutable Fields

Once an entry exists, these fields in `meta.json` are **never** modified by any agent:

- `id`
- `created_at`
- `created_by`
- `supersedes`

Mutating any of these is a protocol violation. If you believe one is wrong, open a challenge.

---

## 4. The Golden Rule: Don't Overwrite, Append or Challenge

**Active entries are read-only for content changes.** If you (an AI) think an `active` entry is wrong, obsolete, or incomplete:

### Path A — Add a Challenge (preferred)
1. Create `challenges/CH-{YYYY-MM-DD}-{entry-id}-{short-slug}.md` using `_schema/challenge-template.md`.
2. In the original entry's `meta.json`, append your challenge ID to the `challenged_by` array. **This is the only allowed edit to an active entry's metadata.**
3. Set the original entry's `status` to `challenged`.
4. Stop. Do not edit `report.md` or `lessons.md` of the active entry.

### Path B — Update Last-Verified (when you confirm it's still correct)
1. Edit only `last_verified` and `last_verified_by` in `meta.json`.
2. No revision snapshot needed for a verification refresh.

### Path C — Curator-Authorized Edits
If Dr. Seidel explicitly authorizes a direct edit in a session, you may edit content — but you MUST:
1. Snapshot the previous state into `revisions/{YYYY-MM-DD}-{agent}-pre-edit.md` BEFORE editing.
2. Note the authorization in the commit message: `authorized-by: Dr. Seidel`.

---

## 5. Creating a New Entry

1. Pick the right `domain`.
2. Generate a stable ID: `KB-{YYYY}-{NNNN}-{kebab-slug}`. Use `_tools/next_id.py` to get the next number.
3. Create folder `<domain>/<slug>/` with:
   - `meta.json` (validated against `_schema/entry.schema.json`)
   - `report.md` (the blueprint / strategy / analysis)
   - `lessons.md` (mistakes, anti-patterns, gotchas)
   - `revisions/{YYYY-MM-DD}-{agent}-initial.md` (snapshot of meta.json + first 200 chars of report.md, for audit)
4. Set `status: proposed` unless you are the curator.
5. Run `python _tools/validate.py` — must pass.
6. Run `python _tools/rebuild_index.py` — regenerates `index.json`.
7. Commit. Never hand-edit `index.json`.

---

## 6. Superseding an Entry

When you want to replace an existing active entry with a better one:

1. Create the new entry following §5, but set `supersedes: <old-id>` in its `meta.json`.
2. In the old entry's `meta.json`:
   - Set `status: superseded`
   - Set `superseded_by: <new-id>`
3. Old entry's content (`report.md`, `lessons.md`) is preserved as-is.

---

## 7. Resolving a Challenge

Only the curator (or an agent explicitly acting on the curator's behalf in-session) resolves challenges.

Resolution = update the challenge file with `resolution: accepted|rejected|partial`, a `resolved_at` date, and a `resolution_notes` field. Then:

- **Accepted** → mark the original entry `deprecated`, optionally create a successor entry with `supersedes`.
- **Rejected** → revert the original entry's `status` to `active`, but keep the challenge file (audit trail).
- **Partial** → create a successor entry with `supersedes`, mark original `superseded`.

---

## 8. Agent Identification

Every write must identify the agent in `meta.json` fields (`created_by`, `last_verified_by`) and in revision filenames.

Use these canonical strings (add a new one only if your model isn't listed):

- `claude-opus-4-7`, `claude-sonnet-4-6`, `claude-haiku-4-5`
- `gpt-5`, `gpt-5-mini`, `codex`
- `gemini-2-5-pro`, `gemini-2-5-flash`
- `deepseek-v3`, `mistral-large`
- `ollama-{model-name}`
- `human:dr-seidel`, `human:{name-slug}`

---

## 9. Commit Message Convention

```
{verb}({entry-id}): short description

verb ∈ {add, verify, challenge, supersede, deprecate, resolve, index, schema, tool, docs}
```

Examples:
- `add(KB-2026-0005): claims rejection rate dashboard pattern`
- `challenge(KB-2026-0001): payer API field changed in 2026-08`
- `supersede(KB-2026-0001 → KB-2026-0012): rewrite with new payer API`
- `verify(KB-2026-0003): still correct as of 2026-09`

---

## 10. Hard Prohibitions

An agent MUST NOT:

1. Delete any file in `revisions/` or `challenges/`.
2. Edit immutable fields (§3).
3. Modify content of an `active` entry without a challenge or curator authorization (§4).
4. Hand-edit `index.json`.
5. Change another agent's revision snapshot.
6. Rewrite `AI_PROTOCOL.md` without an explicit version bump and curator approval.

A protocol violation should be flagged in the commit message and reverted on next session.

---

## 11. Versioning of This Protocol

This protocol is itself versioned. Current version: **v1.0** (2026-05-11).
Bumps require curator approval and an entry in `CHANGELOG.md`.
