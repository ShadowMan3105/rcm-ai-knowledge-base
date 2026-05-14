# AI_PROTOCOL.md — Multi-Agent Contract (v1.2)

**Read this BEFORE writing anything to this repository.**

`AGENTS.md` is also mandatory first-read context. It defines machine-friendly
operating constraints, truth policy, verification gates, Graphify boundaries,
and controlled-tool rules that every AI agent must follow before applying this
protocol.

This file is the contract every AI agent (Claude, GPT, Codex, Gemini, Ollama, etc.) MUST follow when contributing to `rcm-ai-knowledge-base`. The goal is multi-agent safety: any new agent can read, contribute, and challenge prior work without breaking what previous agents established.

---

## 1. Glossary

- **Entry** — a folder under a domain (`automations/`, `research/`, etc.) containing `meta.json`, `report.md`, `lessons.md`, and a `revisions/` subfolder.
- **Domain** — top-level folder grouping related entries.
- **Challenge** — a formal proposal to deprecate or modify an existing `active` entry, stored under `/challenges/`. Used for **substantive** disputes (strategy / correctness).
- **Patch** — a surface correction (typo, dead link, lesson subsequent update) against an entry, stored under `/patches/`. Mergeable on CI green; does NOT question strategy. Introduced in v1.2.
- **Revision** — an immutable snapshot of an entry at a point in time, stored under `<entry>/revisions/`.
- **Curator** — the human (Dr. Seidel) who resolves challenges and approves status changes.
- **Subsequent Update** — an append-only line inside a `### Mistake N` block in `lessons.md` recording new information about the original mistake. Never overwrites the mistake itself.

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

### Path A — Add a Challenge (substantive disputes)
Use when you doubt the **strategy, conclusion, or correctness** of the entry.

1. Create `challenges/CH-{YYYY-MM-DD}-{entry-id}-{short-slug}.md` using `_schema/challenge-template.md`.
2. In the original entry's `meta.json`, append your challenge ID to the `challenged_by` array. **This is the only allowed edit to an active entry's metadata.**
3. Set the original entry's `status` to `challenged`.
4. Stop. Do not edit `report.md` or `lessons.md` of the active entry.
5. Curator (Dr. Seidel) resolves per §7.

### Path B — Update Last-Verified (when you confirm it's still correct)
1. Edit only `last_verified` and `last_verified_by` in `meta.json`.
2. No revision snapshot needed for a verification refresh.

### Path C — Curator-Authorized Edits
If Dr. Seidel explicitly authorizes a direct edit in a session, you may edit content — but you MUST:
1. Snapshot the previous state into `revisions/{YYYY-MM-DD}-{agent}-pre-edit.md` BEFORE editing.
2. Note the authorization in the commit message: `authorized-by: Dr. Seidel`.

### Path D — File a Patch (surface corrections)
Use when the fix is **superficial and does not question the strategy**: typo, dead link, wrong tag, outdated library version in a code example, or appending to a `Subsequent Updates` block in `lessons.md` (see §4.5).

1. Create `patches/PA-{YYYY-MM-DD}-{short-slug}.md` using `_schema/patch-template.md`.
2. Declare `patch_type` from the schema enum (`typo` / `dead-link` / `metadata-fix` / `format-cleanup` / `factual-detail` / `lesson-subsequent-update` / `tag-correction`).
3. Quote the **Before** and **After** text in the patch body.
4. The patch may be merged on CI green; curator review is optional, not required.
5. A patch **must not** delete or rewrite an existing `### Mistake N` block in `lessons.md`. See §4.5.
6. If a reviewer believes the patch is substantive (questions the strategy), they convert it to a challenge per the conversion procedure in the patch template.

### 4.5 — Editing `lessons.md`: Subsequent Updates, never deletions

`lessons.md` is an **append-only ledger of past mistakes**. The whole reason this KB exists is that AIs lose memory across sessions; the historical record of "this mistake was committed" must survive forever — even when the underlying bug, API, or library is later fixed.

Rules:

1. **`### Mistake N` blocks are immutable.** Once committed, a Mistake's heading and its five core fields (`Category`, `Severity`, `What happened`, `Root cause`, `Rule extracted`) MUST NOT be rewritten or removed. Renumbering existing mistakes is forbidden.
2. **New mistakes append.** A new mistake goes at the end as `### Mistake N+1`.
3. **`Subsequent Updates` is append-only.** When the world changes (the library bug is fixed, the API behavior changes, the strategy was refined), append a line to the Mistake's `Subsequent Updates` block via a `lesson-subsequent-update` patch (Path D):
   - Format: `- YYYY-MM-DD by <agent-id>: <what changed; the original Mistake stands>`
4. **Outdated factual details inside an existing update line MAY be replaced** (e.g., a library version that no longer applies), but the Mistake heading and its original five fields stay. That replacement is itself a patch with `applied_to: lessons.md`.
5. **You may add a new Mistake that cross-references an old one** when the same class of error reappeared under different conditions. Reference by ID and Mistake number: `KB-2026-0004#mistake-7`.

A challenge (Path A) is only appropriate when you dispute that the lesson was *correct at the time it was recorded* — extremely rare. The "the world later changed" case is always Path D.

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

1. Delete any file in `revisions/`, `challenges/`, or `patches/`.
2. Edit immutable fields (§3).
3. Modify content of an `active` entry without a challenge, patch, or curator authorization (§4).
4. Hand-edit `index.json`.
5. Change another agent's revision snapshot.
6. Rewrite `AI_PROTOCOL.md` without an explicit version bump and curator approval.
7. Delete, renumber, or rewrite an existing `### Mistake N` block in any `lessons.md` (§4.5).

A protocol violation should be flagged in the commit message and reverted on next session.

---

## 11. Versioning of This Protocol

This protocol is itself versioned. Current version: **v1.2** (2026-05-12).
Bumps require curator approval and an entry in `CHANGELOG.md`.

---

## 12. Lesson Categories, Tag Canon, and Staleness

### 12.1 Mistake categories

Every `### Mistake N` in `lessons.md` declares a `Category` from this closed enum, so an AI can filter relevance fast without reading every lesson body:

`data-quality` · `api-integration` · `library-compat` · `parser` · `schema` · `process` · `strategy` · `security` · `performance` · `configuration` · `deployment`

Adding a new category requires a protocol version bump (curator approval). Mistakes also declare `Severity` (`low` / `medium` / `high`). See `_schema/lessons-template.md` for the cheat-sheet.

### 12.2 Tag canon

`_schema/tags-canonical.json` lists allowed tags per domain plus a global set. `validate.py` emits a **warning** (not error) when an entry uses a tag outside the canon — intentional so genuinely new tags can be introduced. When adding a truly new tag:

1. Add it to `tags-canonical.json` in the SAME PR that adds the entry using it.
2. Place it under the right domain, or under `global` if it spans domains.
3. Tags are lowercase-kebab.

The point of the canon is that the `READ_PROTOCOL.md` ranking step can do clean tag overlaps without semantic drift (`n8n` vs `n8n-workflows` vs `n8n-platform`).

### 12.3 Staleness

`validate.py` emits a warning when an `active` entry has `last_verified` older than 180 days. The entry stays `active` — but ranking in `READ_PROTOCOL.md` §3.4 should treat stale entries as less trustworthy than recently-verified ones. To clear the warning: re-verify against the source and bump `last_verified` + `last_verified_by` (a Path B edit, no challenge needed).

---

## 13. Patches Operational Notes

See §4.D for the procedure. Additional rules:

1. Patches live in `patches/PA-YYYY-MM-DD-slug.md` and follow `_schema/patch.schema.json`.
2. Patches **do not** change the target entry's `status`. An `active` entry stays `active` while patches are applied.
3. Patches must NOT bypass a challenge. If a patch touches multiple paragraphs, rewrites a `Rule extracted`, or changes the strategy of `report.md`, it is a challenge in disguise — stop and open Path A instead.
4. Multiple patches against the same entry are allowed and expected over time.
5. `validate.py` and `rebuild_index.py` track patches; the index exposes a top-level `patches` list and a `stats.open_patches` count.

<!-- GRAPHIFY-KB-LAYER:START -->
## Graphify knowledge graph layer

Graphify is permitted as an advisory navigation and relationship-discovery layer.

Rules:

- Read `AGENTS.md` before using Graphify or changing KB files.
- `AI_PROTOCOL.md`, `AGENTS.md`, generated `index.json`, each entry's `meta.json`, `report.md`, `lessons.md`, `challenges/`, and `patches/` remain authoritative.
- `_graph/` is a cloud-readable advisory snapshot generated locally from governed KB files.
- Graphify outputs must not be used to directly modify immutable fields or active entry content.
- Any graph-derived dispute about correctness must become a challenge.
- Any surface correction must become a patch.
- New reusable strategy must become a governed KB entry with a stable ID.
- Do not ingest PHI, credentials, API keys, payer-specific rates, live operational data, or unreviewed client exports.
- Use `_tools/build_graphify_corpus.py` as the preferred input boundary.
- Use `_tools/update_graph_snapshot.py` to publish controlled `_graph/` snapshots.
- Run `_tools/check_graphify_policy.py`, `_tools/validate.py`, `_tools/rebuild_index.py`, and `_tools/update_graph_snapshot.py --dry-run` before committing integration changes.

Commit policy:

- Do not commit raw generated Graphify outputs.
- Keep `.graphify-kb-corpus/`, `graphify-out/`, `.graphify/`, `.graphify_cache/`, and `.graphify_labels.json` ignored.
- Commit only the controlled `_graph/` snapshot: `README.md`, `GRAPH_REPORT.md`, `graph.json`, and `manifest.json`.
<!-- GRAPHIFY-KB-LAYER:END -->
