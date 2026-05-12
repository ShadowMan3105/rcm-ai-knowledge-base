# Changelog

All notable changes to the KB protocol and repository structure are documented here.
This file is maintained per [AI_PROTOCOL.md](AI_PROTOCOL.md) §11.

Format: each entry is `## [version] — YYYY-MM-DD` followed by sections
`Added`, `Changed`, `Removed`, `Migration notes`.

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
