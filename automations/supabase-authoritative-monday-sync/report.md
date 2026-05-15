# Supabase-Authoritative Monday.com Sync With Dry-Run Ledger And Hold Gates

## Summary

This blueprint describes how to synchronize normalized claim records from Supabase/Postgres into Monday.com without letting Monday become the source of truth. The safe pattern is to treat Monday as an operational surface, generate a no-write plan first, write only verified create/update/link operations, and update the durable ledger only after Monday is re-read and confirmed.

The pattern is designed for claims data that has already passed ingestion, parsing, normalization, dedupe, and durable upload. It should not re-implement the parser or feeder unless a real incompatibility with downstream synchronization is found.

## Context

Operational boards are useful for human work queues, status review, and team visibility, but they are not a durable audit warehouse. They can contain manual fields, stale rows, duplicate rows, wrong grouping, or human-maintained statuses that should not override normalized claim evidence.

Once claim rows exist in Supabase, downstream synchronization should answer a narrow question: what exact Monday create, update, link, skip, or hold action is justified by the durable claim row and by the current Monday item state?

## Approach / Strategy

Start read-only. Inspect the durable claim tables, the destination board schemas, existing item naming, required columns, group structure, relation columns, and any already-stored Monday item ledger fields. Do not assume a column name, board shape, or relation format from memory.

Build a dry-run planner before any write path. The planner reads Supabase final rows, routes records by report status and operational date, looks up existing Monday items, and emits a sanitized action plan. Each row must become exactly one of: create, update, link existing item, skip, or hold.

Use Supabase as the authoritative state. Monday fields can help locate a candidate item, but Monday-only manual fields should not decide the canonical claim status when Supabase already has normalized evidence. For pending work queues, only official paid or denied evidence should close or convert a pending record.

Separate Monday writes from durable ledger writes. At scale, the safest two-step pattern is:

1. Create or update Monday.
2. Re-read the affected Monday item and verify the exact values that matter.
3. Write or align the Supabase ledger only after that re-read passes.

This prevents a successful Monday write from being falsely marked as durable if the later database update fails, and it prevents a database ledger from pointing to an unverified or wrong item.

Hold ambiguous records instead of guessing. Common hold reasons include missing service date, unsupported year or destination board, multiple candidate Monday items, amount mismatch, identity mismatch, relation mapping uncertainty, and wrong-board routing. A hold is a controlled output, not a failure.

## Final Blueprint

### Phase 1: Read-only inventory

Read durable claim counts by status, operational year, and ledger state. Confirm which tables represent final operational claim rows and which report-specific tables are supplementary.

Read each destination board schema from Monday. Capture column IDs, column types, required fields, relation columns, date columns, status columns, and the naming convention for items. Read enough sample items to prove the schema interpretation.

Check whether an existing ledger or cache stores Monday item IDs. If it exists, verify it against current Monday before trusting it. If it does not exist, plan to create one in durable storage rather than adding ad hoc helper columns to Monday.

### Phase 2: Dry-run planner

For each durable final row:

- Determine destination board from canonical status and operational date.
- Build the canonical identity key from claim number, service date, patient identity when available, payer or member evidence when available, and normalized status.
- Search current Monday data for exact and near matches.
- Compare only official synced fields, not manual workflow fields.
- Emit create, update, link, skip, or hold with a reason code.

The dry-run output should include counts by action and small sanitized samples. It should not include patient names, claim numbers, credentials, board IDs, or raw operational data when saved to a general-purpose knowledge base.

### Phase 3: Controlled live proof

Run a one-record or very small write test for each action class that will be used in production. After each write, re-read Monday and verify the exact item ID, group, title, dates, amounts, relation fields, and statuses that were written.

Only after the re-read passes should the durable ledger be updated. If the Monday write succeeds but ledger update fails, run a separate ledger-alignment step that links the verified Monday item to the durable claim row.

### Phase 4: Batch mode

Use small chunks, retry/backoff, sanitized responses, and resumable checkpoints. Avoid storing large raw execution payloads in n8n. Return only proof fields needed for verification.

Use a process-level run lock for large jobs. The lock should live in durable storage or a control table, include heartbeat and expiry, and block another writer from running on the same board and operation. Per-item Monday status columns should be reserved for business state, not for runner locks.

### Phase 5: Ongoing reconciliation

Schedule read-only reconciliation jobs that compare durable ledger state to Monday state. These jobs should identify unlinked rows, stale fields, duplicate candidates, unsupported destination records, and relation mapping gaps. They should not delete automatically.

Duplicate detection should classify exact duplicates, partial duplicates, service-line split artifacts, wrong-board routing, and amount mismatches separately. If Monday contains service-line split rows but Supabase contains the aggregate claim/date row, keep the verified aggregate representation and route the extra operational rows to manual archive or review.

## Results / Verification

The pattern was verified in a live workflow by first completing durable ingestion into Supabase, then synchronizing operational boards from final claim rows. The verified sequence included read-only board/schema inspection, dry-run planning, controlled writes, Monday re-read verification, Supabase ledger alignment, post-write dry-run returning only skips for completed non-paid records, and transient n8n cache checks showing no staged rows left behind.

The process also validated several failure gates: unsupported destination year stays on hold, missing service date stays on hold, amount mismatches are not force-linked, ambiguous candidates are not auto-created over, and pending manual workflow fields are not overwritten by canonical sync.

## Reusable Components

- Supabase final-row query by status, operational year, and ledger state.
- Monday board schema reader with column ID and column type capture.
- Dry-run planner that emits create, update, link, skip, and hold actions.
- Sanitized evidence writer for counts and sample reason codes.
- Monday write runner with small chunks and retry/backoff.
- Monday re-read verifier for created or updated items.
- Separate Supabase ledger alignment runner.
- Run-lock policy with heartbeat, expiry, and checkpoint.
- Duplicate audit classifier that distinguishes true duplicates from service-line split artifacts.
- Relation alias crosswalk planner for payer, practice, or other master-board links.

## Related Entries

- KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser
- KB-2026-0003-universal-claims-ingestion-transient-dedupe

## Tags

n8n, monday-com, supabase, claims-reconciliation, idempotency, deduplication, workflow-design, monday-board, schema-validation

## Date

2026-05

## Status

proposed
