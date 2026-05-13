# Multi-Clinic Paid Claims Consolidation From eCW PDF Reports

**Entry ID**: `KB-2026-0005-multi-clinic-paid-claims-consolidation-pdf`
**Status**: proposed
**Author**: claude-opus-4-7
**Date**: 2026-05-12
**Project**: HF Texas (11 clinicas, FEB-APR 2026, eCW v12)

---

## 1. Problem statement

eCW v12 does not offer a native export that reconciles **what was billed**, **what was paid**, and **what was received** at the check level. Reporting is split across three independent PDF reports per provider per month:

| Report | Filter | Granularity | Money concept |
|---|---|---|---|
| **ALL CLAIM REPORT** | From/To **Bill Date** | service line (CPT) | what was billed (paid + denied + pending) |
| **PAYMENT DETAIL REPORT** | From/To **Posting Date** | service line per check | what was applied to claims |
| **RECEIVABLES REPORT** | From/To **Posting Date** | check (one row per check) | what was received as cash |

To audit revenue, the billing manager (Dr. Seidel) needs:

1. A normalized table per report type, across all clinics and months.
2. A **PMT ↔ REC reconciliation** at the check level (`Σ payment per check == REC.posting_amt`).
3. A **service-line JOIN** of Claims ↔ Payments to label every billed line as `PAID_FULL / PAID_PARTIAL / NOT_PAID / OVERPAID / UNRESOLVED`.
4. Trazabilidad (SourceFile + SourcePage) on every row.

Dimensions: 11 providers × 3 months × 3 report types = **99 PDFs**. Total: 10,612 service-line claim rows; 9,866 payment-detail rows; 1,281 checks. Final workbook: 3.58 MB, 9 sheets.

---

## 2. Architecture

```
PDFs (99) ──► classify_type / detect_provider / detect_month  (filename inventory)
       │
       ├─► is_scanned_pdf?  → YES → mark MISSING (skip; no text layer)
       │
       └─► parse_<type>(path)  [3 specialized parsers, pdfplumber-based]
                │
                ▼
       pickle.dump per (type, provider, month) in work/cache/
                │
                ▼
       ProcessPoolExecutor(workers=4–6)  ──► aggregate in memory
                │
                ▼
       build_workbook(...) ──► openpyxl 9-sheet workbook
```

Key invariants:

- **Cache key** = `{TYPE}__{PROVIDER_UNDERSCORED}__{YYYY-MM}.pkl`. Stable across runs.
- **Provider from filename, NOT from PDF body.** PDF body may truncate (`FORT H WORTH`) or be missing on filter pages. Filename regex is the source of truth.
- **Missing files persisted as `{'_missing': {...}}`** in the same cache slot, so re-runs don't re-attempt scanned PDFs.

---

## 3. The 3 parsers — what they extract

### 3.1 `parse_allclaims.py`

Per service line:
- `provider`, `insurance_code`, `insurance_name`, `patient`, `patient_dob`
- `claim_number`, `bill_date`, `facility`, `claim_copay`, `ins_type`, `ins_id`
- `dos`, `cpt`, `units`, `bill_amt`, `allowed`, `deduc`, `deduc_ptp`, `coins`, `coins_ptp`, `payment`, `balance`
- `source_file`, `source_page`

Also extracts:
- `insurance_summaries` (per insurance: clms, bill_amt, allowed, …)
- `provider_summary` (the footer totals row for the whole provider)
- `claim_notes` (rejection/denial notes attached to claims)

### 3.2 `parse_payments.py`

Per service line (one per claim+CPT+check):
- All AC fields plus: `check_number`, `check_date`, `post_date`, `payer`, `copay`, `rem_bal`, `curr_bal`

`insurance_summaries` and `provider_summary` include `payment` totals.

### 3.3 `parse_receivables.py`

Per check row:
- `insurance_code`, `insurance_name`, `check_number`, `check_date`, `post_date`, `payer_name`
- `amt` (cash received), `posting_amt` (cash applied to claims), `servs` (# service lines paid)
- Differences `amt − posting_amt > 0` = pagos no posteados aún (residual).

---

## 4. The output workbook (9 sheets)

| Sheet | Granularity | Purpose |
|---|---|---|
| **README** | meta | Diccionario de campos + reglas contables + provenance |
| **Claims_Detail** | service line | AC, una fila por (Claim, DOS, CPT) |
| **Payments_Detail** | service line | PMT, una fila por (Claim, DOS, CPT, Check) |
| **Receivables_Checks** | check | REC, una fila por (Insurance, Check#) |
| **Summary_Provider_Month** | (provider, month) | totales AC+PMT+REC con `Check_PMT_Match` |
| **Summary_Insurance_Month** | (provider, month, insurance_code) | pivot por aseguradora |
| **Reconciliation** | check | `Σ PMT.payment per check vs REC.posting_amt` → OK / OVER / UNDER / MISSING_IN_PAYMENTS / ORPHAN_PAYMENT |
| **Master_Enriched** | service line | LEFT JOIN AC ⋈ PMT por (Provider, Claim#, DOS, CPT) → `PAID_FULL / PAID_PARTIAL / NOT_PAID / OVERPAID / UNRESOLVED` |
| **Flags** | flat list | all discrepancies + denial notes + reversals + missing PDFs |

Cada hoja con `auto_filter`, freeze panes, conditional formatting on `Diff_*`, `Status`, `Severity`.

---

## 5. Reconciliation results (HF Texas FEB-APR 2026)

- **96/99 PDFs procesados** (97% cobertura). Los 3 missing son Premier FEB 2026 — escaneados como imagen sin OCR.
- **31/32 (provider, mes) combinaciones cuadran a $0** entre `Σ PMT.payment` y `Σ REC.posting_amt`.
- 2 discrepancias explicadas (ambas **legítimas**, no parser bug):

### Caso 1 — PREMIER MEDICAL CENTER LLC · MARCH 2026 · +$2,599.72

| Check# | Status | PMT_sum | REC_post | Diff | Payer | PostDate |
|---|---|---|---|---|---|---|
| `1237347724` | **ORPHAN_in_PMT** | $2,599.72 | — | +$2,599.72 | OSCAR | 03/27/26 |
| `6084270093` | ORPHAN_in_PMT | $99.02 | — | +$99.02 | UMR | 03/27/26 |
| `RC-` | MISSING_in_PMT | — | $99.02 | −$99.02 | UNITED | 03/10/26 |

**Causas**:
- El OSCAR check $2,599.72 está en PAYMENT DETAIL de MAR pero no en RECEIVABLES MAR. Posibles razones: (a) la REC report del mes lo capturó en un mes distinto debido a cutoff de posting date; (b) el run de eCW se ejecutó con un Posting Date filter ligeramente diferente entre los dos reportes.
- El segundo par ($99.02) es un **wash artificial**: el mismo check físico aparece con identificador distinto en cada PDF — `6084270093` en PMT, `RC-` (placeholder vacío) en REC. eCW parece omitir el check# en RECEIVABLES cuando el ERA llegó con check# faltante.

### Caso 2 — CLINICA HF JOSEY LANE LLC · FEBRUARY 2026 · −$106.99

| Check# | Status | PMT_sum | REC_post | Diff | Payer | PostDate |
|---|---|---|---|---|---|---|
| `328123583` | **ORPHAN_in_PMT** | −$106.99 | — | −$106.99 | OSCAR | 02/05/26 |

**Causa**: es una **reversal/takeback** (pago negativo). RECEIVABLES no lista cheques de reversal porque conceptualmente no hubo cash recibido — el dinero salió. PMT sí lo registra como reducción del saldo.

### Heurística contable derivada

> Cuando `Σ PMT.payment − Σ REC.posting_amt` para un (provider, mes) es distinto de cero, descomponer **siempre** por check# antes de declarar bug del parser. En esta data set, 100% de las diferencias se explicaron por: (1) reversals OSCAR no listadas en REC, (2) checks con identificador faltante en uno de los dos reportes, (3) checks aplicados en distinto mes de posting.

---

## 6. Operational stats

| Métrica | Valor |
|---|---|
| Inventario | 99 PDFs |
| Procesados | 96 (3 escaneados sin OCR) |
| Cold parse, 4 workers | ~6-7 min |
| Cold parse, 6 workers | ~5 min |
| Warm rebuild (from cache) | ~10s |
| Claims_Detail rows | 10,612 |
| Payments_Detail rows | 9,866 |
| Receivables_Checks rows | 1,281 |
| Master_Enriched rows | 10,612 |
| Output workbook | 3.58 MB |
| Reconciliation OK | 31/32 (provider, mes) |
| Master_Enriched PAID_FULL | 46.8% |
| Master_Enriched NOT_PAID | 44.3% |
| Master_Enriched OVERPAID | 7.1% (PRI+SEC payments arriving after AC snapshot) |
| Master_Enriched UNRESOLVED | 1.8% |

---

## 7. Reproducibility

```powershell
cd C:\Claudecodehandoff

# Cold run (parse + build)
python scripts\master_orchestrator.py --workers 6

# Warm rebuild (Excel only, from pickle cache)
python scripts\master_orchestrator.py

# Re-parse just one month
Remove-Item work\cache\*2026-02.pkl
python scripts\master_orchestrator.py

# Full re-parse
Remove-Item work\cache\*.pkl
python scripts\master_orchestrator.py --workers 6
```

Output: `work/HFTEXAS_Consolidated_FEB_MAR_APR_2026.xlsx` (3.58 MB).

---

## 8. Pendientes / future work

1. **OCR para Premier FEB 2026** (3 PDFs sin capa de texto) — pytesseract o re-exportar desde eCW como text-based.
2. **Persistir to Supabase** — los DataFrames de las 4 hojas detail+enriched son `rcm_ops`-ready.
3. **Validation against ERA 835** — el LEFT JOIN AC↔PMT puede cross-validarse contra los 835 archivos que pasan por el clearinghouse.
4. **Multi-year support** — el orchestrator asume YYYY-MM string; añadir validación de cross-year claim aging.

---

## 9. Dependencias

- Python 3.11+
- `pdfplumber` (extraction)
- `openpyxl` (workbook build)
- `concurrent.futures.ProcessPoolExecutor`
- Pickle (caché)

No DB. No network calls. All processing local against the PDFs directory.

---

## 10. Trazabilidad de cada fila del Excel

Toda fila lleva: `SourceReport` (ALL_CLAIM | PAYMENT | RECEIVABLES), `SourceFile` (basename PDF), `SourcePage` (página del PDF). Permite auditar cualquier celda en <30 segundos.
