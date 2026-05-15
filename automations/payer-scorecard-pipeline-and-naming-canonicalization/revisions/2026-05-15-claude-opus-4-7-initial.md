# Revision — Initial commit

**Entry ID**: KB-2026-0009-payer-scorecard-pipeline-and-naming-canonicalization
**Date**: 2026-05-15
**Agent**: claude-opus-4-7
**Action**: initial creation

## meta.json snapshot

```json
{
  "id": "KB-2026-0009-payer-scorecard-pipeline-and-naming-canonicalization",
  "title": "Payer Scorecard pipeline: canonical naming from ERAs/PDFs, alias for ambiguous payers, deterministic performance grading, board_relation gotcha",
  "domain": "automations",
  "kind": "blueprint",
  "status": "proposed",
  "confidence": "high",
  "created_at": "2026-05-15",
  "created_by": "claude-opus-4-7"
}
```

## report.md first 200 chars

# KB-2026-0009 — Payer Scorecard pipeline & naming canonicalization

## Summary

End-to-end design for populating the per-payer monthly scorecard on Monday (board `18410275282`) from exact Supabase

## Notes

Initial entry capturing the Payer Scorecard end-to-end pipeline including the SQL view, the payer_alias crosswalk pattern for ambiguous payer text, the multi-pass payer_id backfill, the deterministic A-F grading, the self-contained writer workflow, and the Monday board_relation column verification gotcha. Six mistakes documented. Status `proposed` until Dr. Seidel reviews.
