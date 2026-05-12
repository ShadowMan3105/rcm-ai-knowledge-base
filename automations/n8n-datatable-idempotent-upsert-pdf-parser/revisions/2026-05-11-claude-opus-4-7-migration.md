---
entry_id: KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser
revision_at: 2026-05-11
revision_by: claude-opus-4-7
change_type: migration
reason: Migrate from meta-schema v1 to entry.schema v2 (stable ID, lifecycle, multi-agent fields).
authorized_by: Dr. Seidel
---

# Revision: initial migration to v2 schema

## Field-level diff (v1 → v2)

| Field | v1 value | v2 value |
|---|---|---|
| (new) id | — | `KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser` |
| (new) kind | — | `blueprint` |
| status | `verified` | `active` |
| (new) confidence | — | `high` |
| date | `2026-05` | (removed; replaced by `created_at`) |
| (new) created_at | — | `2026-05-01` |
| (new) created_by | — | `claude` |
| (new) last_verified | — | `2026-05-11` |
| (new) last_verified_by | — | `claude-opus-4-7` |
| author | `Claude (verified by Dr. Seidel)` | (split into `created_by` + `human_approved_by`) |
| (new) human_approved_by | — | `Dr. Seidel` |
| related | `automations/universal-claims-ingestion-transient-dedupe/` | `KB-2026-0003-universal-claims-ingestion-transient-dedupe` (converted to ID) |

## Pre-migration snapshot of meta.json

```json
{
  "title": "n8n DataTable Workflow Pattern With Idempotent Upsert And PDF Parser Architecture",
  "domain": "automations",
  "date": "2026-05",
  "status": "verified",
  "tags": ["n8n", "datatable", "idempotency", "pdf-parsing", "workflow-design", "source-verification"],
  "summary": "Reusable blueprint for n8n ingestion pipelines that parse vendor PDF reports into a normalized deduplicated cache, with verified DataTable node config, deterministic batch_id idempotency, parallel-branch parser shape, and coordinate-aware PDF extraction.",
  "related": ["automations/universal-claims-ingestion-transient-dedupe/"],
  "author": "Claude (verified by Dr. Seidel)"
}
```

## Content files (report.md, lessons.md)

Unchanged. The migration only updates `meta.json`.
