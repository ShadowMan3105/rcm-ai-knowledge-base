# Paid Date Accounting Reconciliation With PDF Last-Resort Evidence

## Summary

This SOP defines a safe reconciliation pattern for paid-date accounting dashboards when a row or aggregate does not match across operational boards, durable data, cache layers, and source payment reports.

The central decision is source order: payment PDFs are not the first source of truth for routine reconciliation. They are a last-resort evidence layer used only after current structured sources fail to explain the mismatch.

If a PDF proves a payment but the structured systems still do not reconcile, preserve the payment amount and keep the accounting status searchable as mismatched. Do not hide the amount by zeroing it, and do not mark it fully verified until the structured sources also reconcile.

## Problem

Paid-date accounting dashboards often combine several layers:

- operational dashboard rows in Monday or another work surface;
- current paid-claim boards or operational paid tables;
- durable database rows in Supabase/Postgres;
- n8n Data Table caches or workflow outputs;
- payment PDFs from the billing system or payer reports.

These layers can drift. A row can be missing from a current aggregate because of stale cache, a failed sync, payer/practice alias drift, a date-basis mismatch, a deleted or archived operational row, or a payment that exists only in the PDF extract until ingestion catches up.

The unsafe shortcut is to treat "missing from current structured aggregate" as "no payment" and zero or remove the accounting row. That makes dashboards look square while hiding real payment evidence.

## Source Priority

Use this order for paid-date accounting investigations:

1. Current dashboard row and its accounting status.
2. Current paid-claim boards or operational paid tables.
3. Durable Supabase/Postgres payment and claim rows.
4. n8n cache tables and workflow evidence.
5. Payment PDFs, only after the previous layers do not explain the mismatch.

The PDF step is not skipped forever. It is delayed until it is clear that structured sources cannot explain the difference.

## Required Matching Grain

Every comparison must use the same grain:

- paid month derived from check date;
- practice or clinic;
- payer;
- paid claim count;
- paid amount.

Do not compare a service-date month aggregate against a check-date month aggregate. Do not compare payer display names without alias normalization. Do not compare a service-line-level source to an aggregate dashboard row without a declared aggregation rule.

## Workflow

### 1. Capture Current State

Read the dashboard row and capture the item identity, period, practice, payer, paid claims, paid amount, source field, snapshot date, and accounting status.

Also capture a pre-write snapshot before changing anything. If a prior run already changed the row, read the earlier audit payload or immutable run evidence rather than trusting the current row as the original state.

### 2. Rebuild Structured Expected Totals

Rebuild the expected aggregate from the current paid source using check date, practice, payer, claim identity, and amount. Record whether the dashboard row is:

- matched exactly;
- an amount mismatch;
- a claim-count mismatch;
- missing from current paid source;
- duplicated or split;
- held because identity is ambiguous.

### 3. Check Durable Database State

Compare the same key against durable payment and claim rows. Look for:

- payment date or check date missing;
- amount present but not linked to the dashboard aggregate;
- payer/practice alias differences;
- duplicate or split rows;
- ledger state showing a write succeeded in one system but not the other.

### 4. Check n8n Cache and Workflow Evidence

Inspect the cache and workflow evidence before using PDFs. Common explanations:

- cache was built before the current database update;
- replacement cache was partially written or not promoted;
- a workflow mapped the row to a different payer/practice key;
- a previous correction zeroed the row as a hold instead of preserving external evidence.

### 5. Use PDFs as Last-Resort Evidence

Only use PDF extracts when the discrepancy remains unexplained after the structured layers.

When using PDFs, match by check-date month, practice, and payer. Preserve supporting evidence such as source file name, check date, check number, PDF claim count, and PDF amount in an audit payload or cache row. Avoid storing patient names, claim numbers, raw identifiers, board IDs, or live operational amounts in the general knowledge base.

### 6. Write Back the Accounting State

If the PDF confirms a payment but structured sources still disagree:

- write the PDF-backed claim count and amount to the dashboard row;
- keep the accounting status as mismatched or incorrect;
- mark the source field with a PDF cross-check indicator;
- write a cache/audit row that records previous values, desired values, PDF verdict, and post-write verification;
- re-read the dashboard row after the write and verify the exact fields.

If the PDF and the structured sources both reconcile, the row can be marked verified.

If no PDF match exists and structured sources do not support the row, keep or mark the row mismatched and preserve the reason. Do not silently delete or zero without an auditable explanation.

## Status Semantics

Use the accounting status as a search surface:

- Verified: structured sources reconcile at the required grain.
- Mismatched or incorrect: totals do not reconcile, or the row is PDF-backed but structured sources are still missing/stale.
- Audit in progress: temporary state only during a controlled run.

A PDF-backed payment is not automatically "verified" if the paid boards or durable database still disagree. It is evidence that the row should remain visible and investigated.

## Reusable Components

- Paid-date aggregate builder keyed by check-date month, practice, and payer.
- Alias normalization for payer and practice names.
- Pre-write snapshot capture for every affected dashboard row.
- Structured-source dry-run planner with reason-coded outcomes.
- PDF cross-check routine that only runs for unresolved mismatch keys.
- Post-write re-read verifier.
- n8n cache append that records source priority, PDF verdict, previous values, desired values, and verification result.
- Status policy that separates "amount visible" from "structured sources reconciled."

## Verification Criteria

A reconciliation run is not complete until:

- the source priority path is recorded;
- structured totals were rebuilt at the same grain;
- unresolved rows were PDF-checked only after structured checks;
- writes were re-read from the destination surface;
- cache/audit rows were written with sanitized evidence;
- remaining mismatches are searchable by status.

## Related Entries

- `KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser`
- `KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf`
- `KB-2026-0006-supabase-authoritative-monday-sync`
- `KB-2026-0007-denied-claims-refresh-cache-rebuild-strategy`
