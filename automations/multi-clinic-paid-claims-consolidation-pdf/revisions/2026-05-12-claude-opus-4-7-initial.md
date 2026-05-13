# Revision: initial

**Date**: 2026-05-12
**Agent**: claude-opus-4-7
**Action**: initial creation
**Authorized by**: in-session work for Dr. Seidel; status=proposed pending curator approval

---

## meta.json snapshot

```json
{
  "id": "KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf",
  "title": "Multi-Clinic Paid Claims Consolidation From eCW PDF Reports (ALL_CLAIM + PAYMENT + RECEIVABLES)",
  "domain": "automations",
  "kind": "blueprint",
  "status": "proposed",
  "confidence": "high",
  "created_at": "2026-05-12",
  "created_by": "claude-opus-4-7",
  "last_verified": "2026-05-12",
  "last_verified_by": "claude-opus-4-7"
}
```

## report.md first 200 chars

> # Multi-Clinic Paid Claims Consolidation From eCW PDF Reports
>
> **Entry ID**: `KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf`
> **Status**: proposed
> **Author**: claude-opus-4-7
> **Date**: 2026-05-12
> **Project**: HF Texas (11 clinicas, FEB-APR 2026, eCW v12)

## Source code referenced

Pipeline scripts live in `C:\Claudecodehandoff\scripts\`:
- `parse_allclaims.py`
- `parse_payments.py`
- `parse_receivables.py`
- `build_excel.py`
- `master_orchestrator.py`
- `investigate_discrepancies.py` (forensic helper)

Output: `work/HFTEXAS_Consolidated_FEB_MAR_APR_2026.xlsx` (3.58 MB, 9 sheets, 10,612 + 9,866 + 1,281 rows).
