# Changelog

All notable changes to the KB protocol and repository structure are documented here.
This file is maintained per [AI_PROTOCOL.md](AI_PROTOCOL.md) §11.

Format: each entry is `## [version] — YYYY-MM-DD` followed by sections
`Added`, `Changed`, `Removed`, `Migration notes`.

---

## [v1.2] — 2026-05-12

Introduces **patches** (surface-level corrections separate from challenges), **append-only Subsequent Updates** in `lessons.md`, **mistake categorization** with a closed enum, **canonical tags** per domain, and **staleness warnings** for active entries older than 180 days.

### Added
- `_schema/patch.schema.json` — JSON Schema for the YAML frontmatter of files in `patches/`. Patch types: `typo`, `dead-link`, `metadata-fix`, `format-cleanup`, `factual-detail`, `lesson-subsequent-update`, `tag-correction`.
- `_schema/patch-template.md` — copy-paste starter for a patch, with Before/After block and a "this is a patch (not a challenge)" justification checklist.
- `_schema/tags-canonical.json` — canonical tag vocabulary per domain plus a global set. `validate.py` emits a WARNING (not error) on non-canonical tags; new tags must be added here in the same PR.
- `patches/` — open / merged / rejected patches, parallel to `challenges/`.
- `AI_PROTOCOL.md` §4.D — "File a Patch" path for surface corrections that do NOT question the strategy of the target entry.
- `AI_PROTOCOL.md` §4.5 — explicit rules for editing `lessons.md`: `### Mistake N` blocks are immutable; new info appends to a `Subsequent Updates` block; the original mistake stays on the record forever.
- `AI_PROTOCOL.md` §12 — Mistake categories (closed enum), tag canon policy, and staleness threshold (180 days).
- `AI_PROTOCOL.md` §13 — patches operational notes (do NOT change target status, NOT a way to bypass a challenge, multiple patches per entry are allowed).
- `_tools/validate.py` — emits WARNINGS for: (a) active entries with `last_verified` older than 180 days, (b) tags not present in `tags-canonical.json`. Warnings do not fail CI unless `--strict` is passed. Also now validates files under `patches/` against `patch.schema.json`.
- `_tools/rebuild_index.py` — collects patches into a top-level `patches` list in `index.json`, plus `stats.open_patches` and `stats.open_challenges` counts.

### Changed
- `_schema/lessons-template.md` — each `### Mistake N` block now declares `Category` (closed enum) and `Severity` (low/medium/high) and includes an optional `Subsequent Updates` block. Adds an inline cheat-sheet of categories and severity levels.
- `AI_PROTOCOL.md` — version bumped from v1.0 to v1.2 (skipping v1.1, which was a CHANGELOG-only entry from `READ_PROTOCOL.md` introduction).
- `AI_PROTOCOL.md` §1 — glossary now includes `Patch` and `Subsequent Update`.
- `AI_PROTOCOL.md` §10 — Hard Prohibitions adds rules for `patches/` deletion and against renumbering/rewriting existing `### Mistake N` blocks.
- `index.json` — `kb_version` bumped to `2.1`. New `patches` list and new `stats.open_challenges` / `stats.open_patches` counters.
- `README.md` — adds a "Patches vs Challenges" pointer and reflects new repo layout (`patches/`).

### Removed
- Nothing removed. The point of v1.2 is to ADD non-destructive editing paths and make lesson categorization explicit. Existing entries and lessons remain valid; the new fields (`Category`, `Severity`) are recommended but not enforced retroactively (existing lessons keep their original format until a maintainer chooses to refactor them).

### Migration notes
- **Existing entries**: no migration required. The new mistake-category and severity fields apply to lessons written from v1.2 onward. Old `### Mistake N` blocks may stay as-is, but maintainers may add categories/severity via a `format-cleanup` patch over time.
- **Existing tags**: `validate.py` will emit warnings for the first run because the canon was just introduced. The intent is that existing tags will be folded into `tags-canonical.json` as they are encountered, not all at once. Warnings are NOT errors.
- **Existing `last_verified` dates**: entries verified on 2026-05-11 will not warn for staleness until ~2026-11-07 (180-day window).
- **CI behavior**: the workflow `validate.yml` is unchanged. Warnings are advisory. If you want CI to fail on warnings, run `python _tools/validate.py --strict` and adjust the workflow.

---

## [v1.1] — 2026-05-11

Adds the consumer side of the protocol — how AIs *read* and apply prior knowledge.

### Added
- `READ_PROTOCOL.md` — 6-step read flow + canonical raw-content URLs + what to do when an active entry looks wrong.
- `_schema/ai-read-prompt.md` — universal copy-paste system prompt for Claude.ai Projects, ChatGPT Custom GPTs, n8n AI Agents, CLAUDE.md, and API `system` parameters. Includes per-platform setup notes.
- `_tools/query.py` — terminal querying (`--tag`, `--domain`, `--status`, `--search`, `--id`, `--show report|lessons|meta`).

### Changed
- `README.md` — top of the agent section now splits **Reading the KB** vs **Writing to the KB**.

---

## [v1.0] — 2026-05-11

First versioned protocol. Establishes multi-agent safety guarantees.

### Added
- `AI_PROTOCOL.md` — multi-agent contract with lifecycle, immutable fields, challenge/supersede mechanics, and agent-ID canon.
- `_schema/entry.schema.json` (v2) — JSON Schema for `meta.json` with stable IDs, status lifecycle, confidence, audit fields.
- `_schema/challenge.schema.json` — schema for the YAML frontmatter of challenge files.
- `_schema/revision.schema.json` — schema for revision snapshots.
- `_schema/challenge-template.md`, `_schema/meta-template.json` — copy-paste starters.
- `_tools/rebuild_index.py` — regenerates `index.json` from entries and challenges.
- `_tools/validate.py` — validates all entries against schemas (jsonschema or stdlib fallback).
- `_tools/next_id.py` — returns the next available stable KB ID.
- `challenges/` — non-destructive way for any agent to dispute an active entry.
- `<entry>/revisions/` — immutable per-entry audit history.
- `.github/workflows/validate.yml` — CI gate; any PR that fails `validate.py` or whose `index.json` is out of sync is blocked.

### Changed
- `index.json` — now versioned (`kb_version: "2.0"`), includes stats by status/domain/kind and a `challenges` list. **Auto-generated; do not hand-edit.**
- `README.md` — rewritten around the v2 protocol; first instruction is "read AI_PROTOCOL.md".
- `_schema/ai-upload-prompt.md` — v3.0, aligned with protocol v1.0 (canonical IDs, status mapping, validation steps).
- All four existing entries migrated to v2 `meta.json`:
  - `KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser` (active)
  - `KB-2026-0002-rcm-ai-knowledge-base-setup` (active, `kind: meta`)
  - `KB-2026-0003-universal-claims-ingestion-transient-dedupe` (**proposed** — pending curator verification)
  - `KB-2026-0004-rcm-executive-dashboards-hf-2026` (active)

### Removed
- `_schema/meta-schema.json` (v1). Replaced by `_schema/entry.schema.json`.

### Migration notes
- Status mapping applied: `verified → active`, `production → active`, `draft → proposed`.
- `date` (YYYY-MM) split into `created_at` (YYYY-MM-DD) and `last_verified` (YYYY-MM-DD).
- `author` split into `created_by` (canonical agent ID) and `human_approved_by` (free-form name).
- `related` paths converted to KB IDs where the target entry exists in this repo.
- Each migrated entry has a pre-migration snapshot under `revisions/2026-05-11-claude-opus-4-7-migration.md`.
- External consumers reading old field names must be updated.

### Backup
- Tag `backup-2026-05-11-pre-v2-merge` snapshots the state before merging this protocol.
- Mirror at `github.com/ShadowMan3105/rcm-ai-knowledge-base-backup-2026-05-11` (private).
