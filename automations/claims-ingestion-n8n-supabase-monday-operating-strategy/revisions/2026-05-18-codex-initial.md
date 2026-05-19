# Initial Revision - KB-2026-0012

Created: 2026-05-18
Created by: codex

## Metadata Snapshot

```json
{
  "id": "KB-2026-0012-claims-ingestion-n8n-supabase-monday-operating-strategy",
  "title": "Claims Ingestion Operating Strategy From n8n Parser To Supabase And Monday",
  "domain": "automations",
  "kind": "blueprint",
  "status": "active",
  "confidence": "high",
  "created_at": "2026-05-18",
  "created_by": "codex",
  "last_verified": "2026-05-18",
  "last_verified_by": "codex",
  "human_approved_by": "Dr. Seidel"
}
```

## Report Opening Snapshot

This entry records the full operating strategy for claims parsing and synchronization across the current RCM automation stack:

```text
source files or reports
  -> n8n controlled intake/adapters
  -> parser and validation gates
  -> bounded transient staging/cache
  -> Supabase/Postgres durable audit and final rows
  -> dry-run planner
  -> Monday.com operational boards
  -> reread verification and ledger alignment
```
