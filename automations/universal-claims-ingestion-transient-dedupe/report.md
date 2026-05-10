# Universal Claims Ingestion With Transient Cache And Durable Dedupe

## Summary

This entry describes a reusable architecture for ingesting claim-status reports from multiple input channels while preserving auditability, deduplication, and low-token operation. The pattern uses n8n as the orchestration layer, a small transient cache as the staging buffer, and Supabase/Postgres as the durable audit and dedupe store.

The approach is intentionally source-agnostic. It can accept reports produced manually, by external software, or by different AI tools, as long as the workflow normalizes them into the same internal claim, service-line, and file-audit structures.

## Context

Claims ingestion workflows often start as separate parser flows for paid, denied, and pending reports. That works initially, but it creates duplication: every parser has to solve file intake, row normalization, duplicate detection, audit logging, control-total checks, storage, and downstream synchronization.

The better architecture is a universal feeder. Individual adapters may still exist for PDFs, CSVs, manual inputs, or external software exports, but all adapters must converge into one staged, validated, deduplicated ingestion contract before durable storage or downstream board updates.

## Approach / Strategy

The chosen strategy separates ingestion into gates instead of allowing each parser to write directly to downstream systems. The first gate accepts files and records source metadata. The second gate parses and normalizes rows. The third gate validates control totals and row shape. The fourth gate checks durable dedupe keys. The fifth gate writes only missing or changed rows into a transient buffer. The final gate uploads to durable storage, verifies counts and totals, and only then clears transient staging.

This was chosen over direct parser-to-board writes because claim reports can arrive from different sources and with different extraction quality. A direct write path makes every parser responsible for correctness and rollback. A gated universal feeder makes parsing replaceable while preserving the same dedupe, audit, and verification logic.

This was also chosen over storing everything permanently in n8n because n8n Data Tables are better treated as an operational buffer than as a durable audit warehouse. Keeping the transient buffer small reduces workflow risk and cost, while Supabase/Postgres remains the durable source for dedupe history, audit detail, and downstream reconciliation.

## Final Blueprint

Use a universal intake contract. Every input source should produce the same basic metadata: source type, source file name or source label, optional hash when available, report type, ingestion run id, and adapter name. PDFs and CSVs can be first-class sources, but manual and software-fed inputs should enter through the same contract.

Use file-level dedupe before parsing only for exact known file evidence, such as a file hash or previously registered source run. Do not claim row-level dedupe before deterministic parsing. Row-level dedupe requires normalized fields such as report type, source reference, claim reference, service date, row type, and service-line identifiers.

Preserve service-line audit before aggregation. Every parsed CPT or service line should become either a normalized audit row or a fallback/error audit row with enough raw context to diagnose extraction issues. Claim-level or date-of-service-level totals should be derived after this audit layer, not instead of it.

Use source control totals as accuracy gates. When reports include file or provider summary totals, compare parsed totals against those controls before any durable write. If totals fail, retry extraction with stronger local/free methods before marking the batch warning or hold.

Use a transient cache only as a bounded staging buffer. The buffer should hold only rows waiting for durable upload. It should stop accepting new staged data before it approaches the platform size limit, upload verified rows to durable storage, and clear only rows that have been safely uploaded and verified.

Use durable storage for dedupe and audit. A recommended durable layout includes source files, parse batches, parsed claim rows, service-line crosswalk rows, final claim rows, report-specific final tables, parser errors, document totals, and sync runs. Unique keys should live in durable storage, not only in n8n.

Use downstream synchronization only after durable upload succeeds. For example, a separate workflow can compare durable final rows against a work-management board and update stale board records only when durable storage is already correct.

## Results / Verification

The pattern was verified with a real paid-report sample through the safe gates: local file access through a mounted ingestion folder, deterministic parsing, control-total comparison, duplicate-key checks, transient staging, dry-run upload planning, and a controlled durable upload. The workflow was restored to dry-run mode afterward, and transient cache clearing was deliberately left disabled pending a final execution-state review.

Verification focused on row-shape correctness, duplicate-key absence, control-total agreement, durable table counts, and ensuring no downstream board or notification writes occurred during the upload proof.

## Reusable Components

- Universal feeder workflow with adapters for PDF, CSV, and future software-fed inputs.
- Source-file registry for file-level evidence and source-run tracking.
- Parse-batch table for run-level audit.
- Parsed-row audit table for headers, service lines, and aggregated date-of-service rows.
- Claim-to-CPT crosswalk table for service-line traceability.
- Final claim rows table for downstream operational synchronization.
- Report-specific final tables for paid, denied, and pending views.
- Transient staging tables with a hard size cap and clear-after-verify policy.
- Retry ladder for extraction failures before warning/hold status.

## Related Entries

None yet.

## Tags

n8n, supabase, claims-ingestion, deduplication, transient-cache, control-totals

## Date

2026-05

## Status

draft
