# Initial Revision Snapshot

## meta.json

```json
{
  "id": "KB-2026-0006-supabase-authoritative-monday-sync",
  "title": "Supabase-Authoritative Monday.com Sync With Dry-Run Ledger And Hold Gates",
  "domain": "automations",
  "kind": "blueprint",
  "status": "proposed",
  "confidence": "high",
  "created_at": "2026-05-13",
  "created_by": "codex",
  "last_verified": "2026-05-13",
  "last_verified_by": "codex",
  "human_approved_by": null
}
```

## report.md excerpt

This blueprint describes how to synchronize normalized claim records from Supabase/Postgres into Monday.com without letting Monday become the source of truth. The safe pattern is to treat Monday as an operational surface...
