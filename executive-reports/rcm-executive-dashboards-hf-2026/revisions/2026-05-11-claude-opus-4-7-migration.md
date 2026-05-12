---
entry_id: KB-2026-0004-rcm-executive-dashboards-hf-2026
revision_at: 2026-05-11
revision_by: claude-opus-4-7
change_type: migration
reason: Migrate from meta-schema v1 to entry.schema v2.
authorized_by: Dr. Seidel
---

# Revision: initial migration to v2 schema

## Field-level diff

| Field | v1 value | v2 value |
|---|---|---|
| (new) id | — | `KB-2026-0004-rcm-executive-dashboards-hf-2026` |
| (new) kind | — | `blueprint` |
| status | `verified` | `active` |
| (new) confidence | — | `high` |
| (new) created_at | — | `2026-05-01` |
| (new) created_by | — | `human:seidel-delgado` |
| (new) last_verified | — | `2026-05-11` |
| (new) last_verified_by | — | `claude-opus-4-7` |
| author | `Seidel Delgado` | (now `created_by` + `human_approved_by`) |
| summary | em-dash variant | "SQLite a React" (preserved meaning, simplified punctuation) |

## Pre-migration snapshot

```json
{
  "title": "Blueprint: Dashboards Ejecutivos RCM desde SQLite hasta React — HF Multi-Clínica",
  "domain": "executive-reports",
  "date": "2026-05",
  "status": "verified",
  "tags": ["rcm","revenue-cycle","denial-management","claims-analytics","sqlite","react-dashboard","recharts","multi-clinic","timely-filing","cpt-analysis","hispano-medical","dfw","billing-transition","category-ii-cpt","capitation","835-remittance","monday-com","executive-report"],
  "summary": "Pipeline completo SQLite→React para análisis ejecutivo de RCM en grupo médico multi-clínica (12 ubicaciones DFW): 45K+ claims, métricas verificadas, 12 lecciones de errores críticos de datos.",
  "related": ["rcm-operations/denial-tracker-monday-board/","rcm-operations/cpt-gap-analysis/","billing-config/dual-architecture-ikon-ecw/"],
  "author": "Seidel Delgado"
}
```

## Note on related links

The three `related` paths point to entries not yet present in the repo. They are kept as path strings (not IDs) until those entries are created. Convert to KB IDs when they exist.
