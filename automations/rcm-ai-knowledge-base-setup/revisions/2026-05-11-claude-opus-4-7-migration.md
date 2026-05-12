---
entry_id: KB-2026-0002-rcm-ai-knowledge-base-setup
revision_at: 2026-05-11
revision_by: claude-opus-4-7
change_type: migration
reason: Migrate from meta-schema v1 to entry.schema v2; classify as kind=meta since this entry documents the KB itself.
authorized_by: Dr. Seidel
---

# Revision: initial migration to v2 schema

## Field-level diff

| Field | v1 value | v2 value |
|---|---|---|
| (new) id | — | `KB-2026-0002-rcm-ai-knowledge-base-setup` |
| (new) kind | — | `meta` |
| status | `production` | `active` (with `confidence: high`) |
| (new) confidence | — | `high` |
| (new) created_at | — | `2026-05-01` |
| (new) created_by | — | `human:dr-seidel` |
| (new) last_verified | — | `2026-05-11` |
| (new) last_verified_by | — | `claude-opus-4-7` |
| author | `Dr. Seidel` | (now `created_by` + `human_approved_by`) |
| summary | (unchanged base) | Note appended about v2 protocol partial supersession |

## Pre-migration snapshot

```json
{
  "title": "RCM AI Knowledge Base — Setup & Architecture",
  "domain": "automations",
  "date": "2026-05",
  "status": "production",
  "tags": ["github", "knowledge-base", "ai-agents", "blueprints", "lessons", "index", "architecture"],
  "summary": "Public GitHub repo designed for AI-readable knowledge persistence across RCM projects — blueprints, strategies, and lessons learned.",
  "related": [],
  "author": "Dr. Seidel"
}
```

## Note

This entry's `report.md` describes the v1 KB design. It is kept `active` for historical reference. The current authoritative protocol is in `AI_PROTOCOL.md`. A future curator may choose to `supersede` this entry with an updated KB-architecture entry pointing at v2.
