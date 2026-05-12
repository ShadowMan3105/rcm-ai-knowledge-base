---
entry_id: KB-2026-0003-universal-claims-ingestion-transient-dedupe
revision_at: 2026-05-11
revision_by: claude-opus-4-7
change_type: migration
reason: Migrate from meta-schema v1 to entry.schema v2; mapped v1 status=draft to v2 status=proposed with confidence=low.
authorized_by: Dr. Seidel
---

# Revision: initial migration to v2 schema

## Field-level diff

| Field | v1 value | v2 value |
|---|---|---|
| (new) id | — | `KB-2026-0003-universal-claims-ingestion-transient-dedupe` |
| (new) kind | — | `blueprint` |
| status | `draft` | `proposed` |
| (new) confidence | — | `low` |
| (new) created_at | — | `2026-05-01` |
| (new) created_by | — | `codex` |
| (new) last_verified | — | `2026-05-11` |
| (new) last_verified_by | — | `claude-opus-4-7` |
| (new) human_approved_by | — | `null` |
| related | `[]` | `KB-2026-0001-...` (forward-linked to existing related blueprint) |

## Pre-migration snapshot

```json
{
  "title": "Universal Claims Ingestion With Transient Cache And Durable Dedupe",
  "domain": "automations",
  "date": "2026-05",
  "status": "draft",
  "tags": ["n8n", "supabase", "claims-ingestion", "deduplication", "transient-cache", "control-totals"],
  "summary": "Reusable blueprint for multi-source claims ingestion using n8n orchestration, transient staging, durable Supabase dedupe, service-line audit, and control-total validation.",
  "related": [],
  "author": "Codex"
}
```

## Curator action required

Status remains `proposed`. To promote to `active`, Dr. Seidel must verify the blueprint and update:
- `status: active`
- `confidence: high` (or medium)
- `human_approved_by: "Dr. Seidel"`
- `last_verified` / `last_verified_by` to reflect the verification session.
