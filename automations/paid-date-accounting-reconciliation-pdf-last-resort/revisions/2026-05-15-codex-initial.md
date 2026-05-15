# Revision Snapshot - 2026-05-15 - codex

Entry: `KB-2026-0010-paid-date-accounting-reconciliation-pdf-last-resort`

Reason: initial proposed entry created from a live paid-date accounting reconciliation correction.

## meta.json

```json
{
  "id": "KB-2026-0010-paid-date-accounting-reconciliation-pdf-last-resort",
  "title": "Paid Date Accounting Reconciliation With PDF Last-Resort Evidence",
  "domain": "automations",
  "kind": "sop",
  "status": "proposed",
  "confidence": "high",
  "created_at": "2026-05-15",
  "created_by": "codex",
  "last_verified": "2026-05-15",
  "last_verified_by": "codex",
  "human_approved_by": null,
  "tags": [
    "n8n",
    "monday-com",
    "supabase",
    "datatable",
    "claims-reconciliation",
    "payment-detail",
    "source-verification",
    "data-quality",
    "sop",
    "sync"
  ],
  "summary": "Reusable SOP for reconciling paid-date accounting totals across Monday, Supabase, n8n caches, paid-claim boards, and payment PDFs. The key rule is to use PDFs only as last-resort evidence after structured sources fail, then preserve both the PDF-backed amount and the searchable mismatch status until the structured sources reconcile.",
  "related": [
    "KB-2026-0001-n8n-datatable-idempotent-upsert-pdf-parser",
    "KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf",
    "KB-2026-0006-supabase-authoritative-monday-sync",
    "KB-2026-0007-denied-claims-refresh-cache-rebuild-strategy"
  ],
  "supersedes": null,
  "superseded_by": null,
  "challenged_by": [],
  "deprecated_reason": null
}
```

## report.md opening

```md
# Paid Date Accounting Reconciliation With PDF Last-Resort Evidence

## Summary

This SOP defines a safe reconciliation pattern for paid-date accounting dashboards when a row or aggregate does not match across operational boards, durable data, cache layers, and source payment reports.
```
