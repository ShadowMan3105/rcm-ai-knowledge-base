# Claims Ingestion Operating Strategy From n8n Parser To Supabase And Monday

## Summary

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

The rule is simple: n8n orchestrates, Supabase/Postgres preserves truth, and Monday is the human operations surface. A parser may adapt to many file types, but no parser should directly turn an uncertain extraction into a Monday write.

This entry consolidates the strategy already used across the n8n DataTable parser pattern, universal claims ingestion, Supabase-authoritative Monday sync, denial refresh, paid-claim reconciliation, and payment-detail accounting work. It does not replace those entries; it gives future agents a single operating map for the full path.

## Context

Claims files arrive in several forms: paid reports, denied reports, pending reports, all-claim exports, payment detail reports, spreadsheets, and provider/payer-specific PDFs. Some sources have service-line detail, some have claim/date-of-service totals, some include payment/check controls, and some are useful only as support evidence.

The system must therefore handle two risks at the same time:

1. Extraction risk: the parser can misread rows, collapse service dates, lose CPT/service lines, or fail control totals.
2. Sync risk: a correct durable row can still be written to the wrong board, wrong group, wrong item, or wrong ledger link if Monday is not re-read and verified.

The architecture prevents both risks by splitting parsing, durable upload, and Monday sync into separate gates.

## Authority Model

### n8n

n8n is the orchestrator and bounded staging layer. It should run controlled workflows, adapters, retry ladders, Data Table staging, cache refreshes, and sanitized runner responses. It should not be treated as the permanent claims warehouse.

### Supabase/Postgres

Supabase/Postgres is the durable authority for source files, parser runs, service-line audit, final claim rows, report-specific final tables, check/payment evidence, dedupe keys, sync ledgers, and process locks. If there is a conflict between Supabase final rows and Monday manual state, Supabase-backed evidence wins unless the user explicitly approves a correction.

### Monday.com

Monday.com is the operational work surface for staff. It is used for visibility, workflow status, ownership, follow-up, and management review. Monday should be synchronized from durable rows after dry-run planning and reread verification. Manual Monday fields should not overwrite official paid, denied, or pending evidence.

## End-to-End Blueprint

### 1. Intake and source registration

Every file or report enters through a controlled n8n intake path. The intake layer records source metadata before parsing:

- source type
- report type
- original file name or source label
- source hash or stable file signature when available
- adapter name and version
- ingestion run id
- user-approved scope if the run is scoped by date, practice, payer, or report set

Only exact source/file evidence can be deduped before parsing. Row-level dedupe starts after deterministic normalization.

### 2. Adapter and extraction layer

Adapters normalize each source into the same parser contract. PDF, spreadsheet, webhook, manual, and software-export adapters can differ internally, but they must converge into the same output classes:

- file header or source metadata rows
- service-line audit rows
- claim/date-of-service total rows
- report/payment/check control totals
- parser warnings and parser errors

Use coordinate-aware extraction for tabular PDFs when the parser depends on column position. Markdown or plain text extraction can be a preview or fallback, but it is not enough proof for columnar financial sources unless controls pass.

### 3. Service-line audit before aggregation

Do not aggregate away CPT or service-line evidence at extraction time. The parser may publish claim/date-of-service operational totals, but every source service line should first become an audit row or an explicit fallback/error row.

Recommended row layers:

- `source_files`: one row per source evidence object.
- `parse_batches`: one row per parser run.
- `parsed_claim_rows`: normalized headers, service lines, and date-of-service totals.
- `service_line_crosswalk`: CPT/service-line traceability and rollup evidence.
- `claim_rows_final`: durable operational final rows by claim/date-of-service/status.
- report-specific final tables such as paid, denied, and pending final views.
- payment/check tables where the source evidence is payment or remittance oriented.

### 4. Control-total gate

When a source includes totals, the parser must compare parsed totals against the source controls before durable writes:

- row counts
- billed amount totals
- allowed amount totals
- paid amount totals
- denied or pending counts
- check/payment totals when present

If controls fail, retry extraction with stronger local/free methods before marking the batch warning or hold. A failed control total blocks durable upload unless the user explicitly approves a bounded exception.

### 5. Transient staging in n8n

n8n Data Tables are used only as bounded staging or cache surfaces. They are useful for:

- current-run staged rows
- parser warnings/errors
- cache snapshots used to reduce repeated live reads
- temporary payloads before verified durable upload

They are not durable audit storage. Keep the transient buffer small. Clear staged rows only after durable upload proof exists. If a cache cannot be refreshed in place with available tools, archive the old table and create a fresh versioned cache from Supabase.

### 6. Durable upload to Supabase/Postgres

The upload workflow writes source, batch, audit, crosswalk, final, and report-specific rows in an explicit order:

1. Register source file or source run.
2. Register parse batch.
3. Upload service-line/audit rows.
4. Upload or align crosswalk rows.
5. Derive and upload final operational rows.
6. Verify durable counts, duplicate keys, and control totals.
7. Only after verification, mark transient rows clearable.

Use persisted key columns such as `dedup_key`, `crosswalk_key`, and `final_key` rather than recomputing identity downstream. Recomputed keys can lose modifiers or renamed fields.

### 7. Final-row policy by report type

Paid, denied, and pending reports do not mean the same thing.

- Paid rows are monetary and must preserve paid, allowed, check/payment, payer, practice, and service-date evidence.
- Denied rows are denial/status evidence and normally have paid amount zero or null.
- Pending rows are transmission/status evidence and should not be treated as payment accounting.

The operational unit for current paid, denied, and pending rows is claim number plus date of service, with service-line evidence preserved separately. Do not collapse multi-DOS claims into one final row.

### 8. Monday dry-run planner

Monday sync starts only after durable final rows are verified. The planner reads current Supabase final rows and current Monday board state, then emits a no-write action ledger:

- create
- update
- link existing item
- skip
- hold
- resolve or archive candidate when the user-approved source scope supports it

Each action needs a reason code. Common hold reasons include missing service date, unsupported destination year, multiple candidate items, amount mismatch, stale stored Monday item id, wrong-board routing, relation uncertainty, missing master-board alias, or parser-control failure.

### 9. Controlled Monday writes

Before live writes:

- re-read destination board schemas
- capture current column IDs and types
- verify item identity and group routing
- run a small proof batch for each action class
- use controlled tools or wrappers instead of free-form production GraphQL

After each write:

1. Re-read the affected Monday item.
2. Verify the exact business fields that matter.
3. Update the Supabase ledger only after the re-read passes.

This prevents a Monday mutation success response from being treated as final proof.

### 10. Pending-board rule

Pending reconciliation is one-way from official evidence. A pending item can be changed only when official paid or denied evidence proves that it moved. Manual pending-board fields, internal workflow statuses, and follow-up notes are not official evidence and should not be used to change the same pending record.

### 11. Cache and low-token operation

For reporting and research, prefer an existing verified n8n cache before live reads. If no suitable cache exists, create or refresh a cache as part of the work. For production writes, caches can accelerate discovery but must not replace live read verification of the system being written.

### 12. Large-run controls

Large jobs need process-level safeguards:

- board/process scoped lease lock
- heartbeat and expiry
- resumable checkpoint
- small chunks
- retry/backoff
- sanitized runner responses
- post-write dry-run returning zero pending safe actions

Do not use per-item Monday statuses as the primary automation lock. Business status fields should represent business state, not runner bookkeeping.

## Required Verification Gates

Before calling an ingestion or sync run complete, prove:

1. Source inventory is known.
2. Parser output row counts match expected source controls or documented holds.
3. Service-line audit rows exist before aggregation.
4. Duplicate keys are zero or explicitly classified.
5. Supabase durable counts and totals match upload expectations.
6. n8n transient rows are cleared only after durable proof.
7. Monday writes were planned by dry-run first.
8. Monday writes were re-read and verified.
9. Supabase ledger updates happened only after Monday re-read proof.
10. Final dry-run returns no remaining safe write actions, or lists remaining holds clearly.

## What Must Not Go Into This KB

Do not include PHI, raw claim numbers, patient names, member IDs, credentials, API keys, internal tokens, exact live claim lists, payer-specific confidential rates, or full board exports. Store those in local evidence folders or protected durable systems, not in the general KB.

## Related Entries

- KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser
- KB-2026-0003-universal-claims-ingestion-transient-dedupe
- KB-2026-0006-supabase-authoritative-monday-sync
- KB-2026-0007-denied-claims-refresh-cache-rebuild-strategy

## Status

Active. Created after curator request to preserve the complete n8n -> Supabase -> Monday claims parsing and sync operating strategy in GitHub before a PC reinstall.
