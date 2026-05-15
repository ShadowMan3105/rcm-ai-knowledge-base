# Denied Claims Refresh With Supabase Authority, Monday Resolution, And Cache Rebuild

## Summary

This blueprint records the verified strategy for refreshing denied claims from a new official report set. The successful pattern is: read the current KB and repo state first, parse current denial reports into deterministic claim-and-DOS keys, compare against live Supabase and Monday in dry-run mode, execute only safe writes with backups, re-read both systems, and rebuild n8n Data Table caches by versioning when the old cache cannot be refreshed in place.

The core rule is that official report evidence updates the durable operational layer, while Monday remains the human workflow surface. n8n Data Tables are useful cache surfaces, but if a cache cannot be updated cleanly, archive it and create a fresh cache instead of appending duplicate or stale rows.

## Context

Denied-claim reports are periodic snapshots. If a denial existed in an older snapshot but no longer appears in the latest official report for the same refreshed scope, it should be treated as resolved for operational purposes. The durable operational layer should no longer carry it as current, and Monday can mark the item worked or resolved for staff visibility.

The difficult part is avoiding false cleanup. A missing row can mean "resolved," but it can also mean the wrong date scope, missing source file, parser drift, duplicate key, stale cache, or incomplete live read. This strategy prevents those mistakes by making source controls, dry-run counts, duplicate checks, backups, writes, and post-write re-reads explicit gates.

## Approach / Strategy

Start by reading the current knowledge repo and current production state. Do not rely on an older checkout, local snapshot, memory, or an unverified cache when writing back to the KB or to production systems.

Parse the uploaded denied-claim reports into normalized denied rows. Use the official report rows as source evidence and build a deterministic operational key from claim number plus service date, with supporting patient, payer, practice, source file, and amount fields used for verification and collision review.

Apply the user-approved service-date scope exactly. Files included in the upload define the refreshed practice/report scope; rows outside the user-approved DOS range are not added as current denials for that run.

Read live Supabase operational denial rows and the live Monday Denials board before any write. Existing n8n caches may speed up research, but production writes require live re-read evidence because caches can lag.

Build a dry-run ledger with these action classes:

- `add`: present in the latest report but absent from current Supabase/Monday.
- `update`: present in both places but official fields differ.
- `resolve`: active in Supabase/Monday for the refreshed scope but absent from the latest report.
- `hold`: duplicate, ambiguous, missing claim/date, out of scope, or schema mismatch.

Do not write if there are unresolved holds. A hold is a valid safety output, not a failure.

Before writes, save a local backup of all affected Supabase rows and Monday item identifiers. Then execute writes in an idempotent order:

1. Ensure needed Monday items exist.
2. Insert or patch current operational Supabase rows.
3. Patch official Monday fields for matching active rows.
4. Mark stale Monday rows resolved.
5. Remove stale rows only from operational/current Supabase tables, not from raw or audit history.
6. Re-read Supabase and Monday and prove that the dry-run ledger returns zero pending actions.

If a write fails halfway, do not restart blindly. Re-read live state, classify what already succeeded, and continue idempotently from the new state. This prevents duplicate Monday items or double inserts after partial success.

For n8n Data Table caches, prefer a true refresh if the tool supports it. If the available Data Table interface only supports appending rows, do not append a duplicate cache. Archive the old table with a dated name and create a new versioned cache from the verified Supabase state.

## Final Blueprint

### Inputs

- Current official denied-claim report files.
- Explicit DOS range approved by the user.
- Current Supabase operational denial tables.
- Current Monday Denials board state.
- Existing n8n cache metadata, used only to decide whether cache refresh is possible.

### Safety Gates

1. Current KB/repo state has been read before writing a KB update.
2. Source files are inventoried and at least one rendered or text-verified report proves the report type and report date.
3. Parser produces denied rows with no duplicate active claim-number-plus-DOS keys.
4. Supabase and Monday are re-read live before production writes.
5. Dry-run action counts are saved.
6. Holds are zero, or the run stops.
7. Backups or before-snapshots exist before writes.
8. Writes are idempotent and can resume after partial success.
9. Post-write dry-run returns zero pending add/update/resolve/hold actions.
10. Cache refresh is versioned if in-place update/delete is unavailable.

### Supabase Policy

Supabase/Postgres is the durable authority for current operational state and historical audit. Current operational denial rows may be inserted, patched, marked inactive, or deleted according to the approved cleanup policy. Raw parser/audit history should not be deleted during an operational refresh.

When the user prefers saving space, delete only from operational current tables after backup and verification. Keep source/audit evidence available for traceability unless the user separately approves audit retention cleanup.

### Monday Policy

Monday is the human workflow board. New active denials are created or updated there after live schema reads. Denials absent from the latest official report in the refreshed scope are marked resolved/worked rather than deleted, preserving staff visibility.

Do not assume Monday column IDs from memory. Read the live board schema or derive update payloads only from columns already proven to exist. If a mutation fails because a column does not exist, remove that field from the controlled mapping, re-read live state, and continue idempotently.

### n8n Cache Policy

n8n Data Tables are bounded cache/staging surfaces. They are not the durable claims warehouse. If a denial cache cannot be cleanly refreshed in place by the available tools, archive the table and create a fresh versioned cache from Supabase current rows.

The new cache should include a run ID, source agent, cache key, claim/DOS fields, Monday link fields, current flag, and serialized payload evidence. It should be rebuilt from verified Supabase state, not from an older cache.

## Results / Verification

This strategy was verified in a live denied-claim refresh. The run parsed the current report set, scoped it by service date, generated a dry-run ledger, wrote only safe actions, recovered from partial Monday success after schema errors, updated Supabase and Monday, removed stale operational Supabase rows, marked stale Monday items resolved, and re-read both systems until the comparison returned zero pending actions.

The n8n denial cache was then rebuilt by archiving the old cache and creating a fresh version from current Supabase denial rows. The cache rebuild evidence showed the old table renamed, the new table created, and current denial rows loaded without appending to stale cache data.

## Reusable Components

- PDF/text extraction proof before parsing.
- DOS-scoped denied-row parser output.
- `claim_number + DOS` active denial comparison key.
- Dry-run ledger with add/update/resolve/hold classes.
- Backup-before-write artifact.
- Idempotent resume after partial write success.
- Supabase operational row insert/patch/delete runner.
- Monday create/update/resolve runner with live schema-safe column mapping.
- Post-write re-read comparator.
- n8n Data Table archive-and-recreate cache rebuild runner.

## Related Entries

- KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser
- KB-2026-0003-universal-claims-ingestion-transient-dedupe
- KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf

## Tags

n8n, monday-com, supabase, datatable, transient-cache, claims-reconciliation, denials, denial-management, source-verification, schema-validation, workflow-design

## Date

2026-05

## Status

active
