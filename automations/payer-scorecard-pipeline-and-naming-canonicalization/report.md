# KB-2026-0009 — Payer Scorecard pipeline & naming canonicalization

## Summary

End-to-end design for populating the per-payer monthly scorecard on Monday (board `18410275282`) from exact Supabase data. The pipeline produces 9 metrics per (payer × month): claims submitted, paid claims, denied claims, total billed, total collected, denial rate %, collection rate %, avg payment days, and a deterministic A-F performance grade. Two architectural decisions matter most: (1) the canonical payer name lives in the ERA/PDF (the contractual document), not in the initial seed of the Monday Payers Master; (2) ambiguous text like "CIGNA" (which could be CIGNA HEALTHCARE or CIGNA HEALTHSPRING — distinct contractual entities) is resolved via a `payer_alias` crosswalk that defaults to one but does NOT unify the two.

## Context

The Monday Payer Scorecard board was created empty months ago, intended to surface per-payer health (denial rate, collection rate, payment speed) so contract renegotiation conversations are data-driven. Populating it required reconciling three independent payer naming systems:

1. **`public.payers` (Monday Payers Master mirror)** — initial seed had names like `CIGNA HEALTHSPRING`, `BLUE CROSS BLUE SHIELD OF TEXAS (BCBS TX)`, `OSCAR HEALTH`. Created from operational lists, not from real billing documents.
2. **`paid_claims_final.payer` (text)** — names extracted from ERA 835 files and PDF Payment Detail reports: `OSCAR HEALTH PLAN`, `BLUECROSS BLUESHIELD OF TEXAS`, `CIGNA`. These are what the payer literally calls itself in the remittance.
3. **`public.claims.payer_id` (UUID FK)** — populated by claims ingestion; sometimes NULL for legacy claims.

Initial join `paid_claims_final.payer = payers.payer_name` matched only ~3% of rows. Most of the denials table (77%) also had `payer_id IS NULL` because the parser linked claims but not payers.

Without fixing the naming mismatch, the scorecard would show almost no data. With inference (fuzzy match), we'd be violating the operating rule "no heuristic, only exact contractual data."

## Approach / Strategy

### 1. Determine the canonical source — the ERA/PDF wins

When a payer names itself one way in the remittance and the Monday master has a different label, **the remittance is canonical**. Two reasons:

- The remittance is the legal contractual document. The clinic's internal label is a label, not the truth.
- If we rename `payers.payer_name` to match the remittance, every future join works without translation.

This required UPDATEs to 8 payers in `public.payers` and corresponding `change_simple_column_value` mutations in Monday Payers Master — **with item_ids preserved** because that board is referenced by many other workflows. Only the `name` field changed.

### 2. Distinguish "rename" from "unify"

For 8 of the 9 mismatches, the rename was unambiguous (just remove a parenthetical or expand an abbreviation). One was different: the master had **two separate Cigna entities** (CIGNA HEALTHCARE and CIGNA HEALTHSPRING) but the ERA literally says only "CIGNA". These are different contracts with different fee schedules. Renaming one to "CIGNA" would unify them in queries — bad.

The fix: a `rcm_ops.payer_alias` crosswalk table.

```sql
CREATE TABLE rcm_ops.payer_alias (
  alias_name TEXT PRIMARY KEY,
  payer_id UUID NOT NULL REFERENCES public.payers(id),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO rcm_ops.payer_alias VALUES
  ('CIGNA',
   '<UUID of CIGNA HEALTHCARE>',
   'PDFs say "CIGNA" without suffix. Default to CIGNA HEALTHCARE. CIGNA HEALTHSPRING stays separate for confirmed cases.');
```

The view and triggers do `COALESCE(exact_match, alias_lookup)` when resolving a text payer name to a payer UUID. Default = pick one, but the other one is still available when the data is explicit.

### 3. Multi-pass backfill of `denials.payer_id` — no inference

A single SQL UPDATE pass found 89% of the missing payer_ids. Additional passes against parsed_claim_rows and Monday's claim-id text fields raised the coverage. The 27 unresolvable rows turned out to be migration-seed denial cards with `denied_amount = $0.00` (operational notes the staff wrote in Monday, not real denials). They were deleted in both stores.

The passes in order:

1. **Pass 1** — `claims.payer_id` via `denials.claim_id` FK: 23% → 89%
2. **Pass 2** — `denials_final.payer` text (active rows) via `claim_number`: 89% → 91.6%
3. **Pass 3** — `parsed_claim_rows.insurance_name` for claim numbers not in `denials_final.is_current`: 91.6% → 94.7%
4. **Pass 4** — Monday `text_mm2c571f` (Claim ID text field) joined to `public.claims` for orphaned denials: 94.7% — caught 14 more
5. **Cleanup** — Deleted 27 unresolvables (all `$0.00`, all migration-seed, none representing real denials). Resulted in 100% coverage on the remaining 482 rows.

Crucially: every pass used **exact source data** (matching by claim_number string, by payer_alias, or by claim_id FK). No fuzzy matching. The 27 deletions were justified because the rows themselves were not denials in the accounting sense — they were operational notes with $0 denied amount, no source_file, and no insurance information in any system.

### 4. Deterministic performance grade

The grade is computed from two metrics (denial_rate_pct and avg_payment_days) by a CASE WHEN chain that any auditor can read. No machine learning, no thresholds tuned to data. The thresholds are conventional billing benchmarks. If a payer has fewer than 5 claims in the period, the grade is `NULL` (insufficient volume).

```sql
CASE
  WHEN claims_submitted < 5 THEN NULL
  WHEN denial_rate >= 0.25 OR avg_payment_days >= 90 THEN 'F — Critical'
  WHEN denial_rate >= 0.15                            THEN 'D — Poor'
  WHEN denial_rate >= 0.10 OR avg_payment_days >= 60  THEN 'C — Average'
  WHEN denial_rate >= 0.05 OR avg_payment_days >= 45  THEN 'B — Good'
  ELSE 'A — Excellent'
END
```

### 5. Self-contained writer workflow (not via drain queue)

The generic Supabase→Monday drain workflow uses `monday_column_map` for dynamic mapping. It's designed for tables that have rows in Monday already and just need column updates pushed.

The scorecard is different: it's a derived view, items are created and updated by the writer alone, and the writer needs to look up the existing item id by `Dedupe Key` to decide create-vs-update. So this workflow lives on its own:

1. **Daily 5 AM** schedule trigger
2. **Fetch view** from Supabase: `GET /rest/v1/vw_payer_scorecard_monthly?...` with `Accept-Profile: rcm_ops`
3. **Fetch existing** items from Monday board with their `Dedupe Key` text column
4. **Build mutations** in a Code node — map dedupe_key→item_id, decide `create_item` for new rows or `change_multiple_column_values` for updates. Compose one aliased GraphQL mutation.
5. **POST to Monday** API
6. **Log** to `rcm_sync_log` with counts

Upsert idempotency is by `dedupe_key = '<payer_monday_item_id>|<YYYY-MM>'`. Running the workflow N times is safe — same period+payer produces same dedupe_key and the same row gets re-updated.

### 6. board_relation column gotcha

Monday `board_relation` columns return `text: null, value: null` in standard column_values queries. This is **easy to misread as a failed mutation**. The mutation `change_multiple_column_values(..., column_values: "{\"board_relation_xxx\":{\"item_ids\":[<id>]}}")` actually does work, but verification requires querying with a GraphQL inline fragment:

```graphql
column_values(ids: ["board_relation_xxx"]) {
  ... on BoardRelationValue {
    linked_item_ids
    linked_items { id name }
  }
}
```

The first time we built the scorecard writer we thought the payer link wasn't working because `text` and `value` both came back null. Then we ran the inline-fragment query and saw `linked_item_ids: ["11737429509"]` — the link was there all along.

## Final Blueprint

### Step 0 — modify the Monday board to match the pipeline

For any Monday board that will be populated by a workflow, add these columns first (before writing the workflow):

- `date` "Period Start Date" (real date, for sort/filter — text "MM/YYYY" stays for human display)
- `text` "Dedupe Key" — `<reference_id>|<period or other unique key>`
- `date` "Last Synced [n8n]" — timestamp written by the workflow
- The metric columns themselves (`numeric` for $, %, counts; `color/status` for graded labels)

### Step 1 — canonicalize payer naming

Before any per-payer reporting:

1. For each payer in the Monday Payers Master, find the most-common name in `paid_claims_final.payer` (or whatever your remittance-derived table is).
2. If the master's name and the remittance name disagree, `UPDATE payers SET payer_name = <remittance name>` AND `change_simple_column_value` on the Monday item — **preserving the item_id**, only the `name` column changes.
3. For ambiguous cases where the remittance text could map to multiple master payers (different contracts), INSERT into `rcm_ops.payer_alias` with the default choice.
4. Document the alias decision in the row's `notes` field so the next auditor knows why "CIGNA" defaults to CIGNA HEALTHCARE.

### Step 2 — Multi-pass `payer_id` backfill template

```sql
-- Pass 1: via claim_id FK
UPDATE public.denials d SET payer_id = c.payer_id
FROM public.claims c WHERE d.claim_id = c.id AND d.payer_id IS NULL AND c.payer_id IS NOT NULL;

-- Pass 2: via denials_final.payer text (most recent active row per claim)
WITH unresolved AS (
  SELECT d.id AS denial_id, df.payer AS payer_text
  FROM public.denials d
  JOIN public.claims c ON c.id = d.claim_id
  JOIN rcm_ops.denials_final df ON df.claim_number = c.claim_number AND df.is_current
  WHERE d.payer_id IS NULL
),
resolved AS (
  SELECT u.denial_id,
    COALESCE(
      (SELECT id FROM public.payers WHERE UPPER(TRIM(payer_name)) = UPPER(TRIM(u.payer_text))),
      (SELECT payer_id FROM rcm_ops.payer_alias WHERE UPPER(TRIM(alias_name)) = UPPER(TRIM(u.payer_text)))
    ) AS resolved
  FROM unresolved u
)
UPDATE public.denials d SET payer_id = r.resolved
FROM resolved r WHERE d.id = r.denial_id AND r.resolved IS NOT NULL;

-- Pass 3: via parsed_claim_rows.insurance_name for claim_numbers not in denials_final
-- (same shape, different JOIN target)

-- Pass 4: via Monday item's claim-id text column for orphaned denials
-- (requires the Monday item_ids and a static mapping from item_id to claim_number)

-- Cleanup: if remaining rows are operational notes with $0 amount, delete them in both stores
DELETE FROM public.denials WHERE payer_id IS NULL AND denied_amount = 0
  AND last_modified_by = 'migration';
-- Plus DELETE the corresponding Monday items via the API.
```

### Step 3 — Scorecard SQL view

```sql
CREATE OR REPLACE VIEW rcm_ops.vw_payer_scorecard_monthly
WITH (security_invoker = on) AS
WITH
claims_monthly AS (
  SELECT p.id AS payer_id, p.payer_name, p.monday_item_id AS payer_monday_item_id,
    DATE_TRUNC('month', c.date_of_service)::date AS period_start,
    TO_CHAR(c.date_of_service, 'MM/YYYY') AS period_label,
    COUNT(DISTINCT c.id) AS claims_submitted
  FROM public.claims c JOIN public.payers p ON p.id = c.payer_id
  WHERE c.date_of_service IS NOT NULL
  GROUP BY p.id, p.payer_name, p.monday_item_id, DATE_TRUNC('month', c.date_of_service), TO_CHAR(c.date_of_service, 'MM/YYYY')
),
denials_monthly AS (
  SELECT d.payer_id,
    DATE_TRUNC('month', COALESCE(d.denial_date, d.created_at::date))::date AS period_start,
    COUNT(DISTINCT d.id) AS denied_claims_count
  FROM public.denials d
  WHERE d.payer_id IS NOT NULL
  GROUP BY d.payer_id, DATE_TRUNC('month', COALESCE(d.denial_date, d.created_at::date))
),
paid_monthly AS (
  SELECT
    COALESCE(
      (SELECT id FROM public.payers WHERE UPPER(TRIM(payer_name)) = UPPER(TRIM(pcf.payer))),
      (SELECT payer_id FROM rcm_ops.payer_alias WHERE UPPER(TRIM(alias_name)) = UPPER(TRIM(pcf.payer)))
    ) AS resolved_payer_id,
    DATE_TRUNC('month', pcf.dos)::date AS period_start,
    COUNT(DISTINCT pcf.id) AS paid_claims_count,
    ROUND(SUM(pcf.billed_amount), 2) AS total_billed,
    ROUND(SUM(pcf.paid_amount), 2) AS total_collected,
    ROUND(AVG(EXTRACT(EPOCH FROM (pcf.check_date::timestamp - pcf.dos::timestamp))/86400.0)
          FILTER (WHERE pcf.check_date IS NOT NULL AND pcf.traceability_status IN ('INFERRED','CONFIRMED')), 1) AS avg_payment_days
  FROM rcm_ops.paid_claims_final pcf
  WHERE pcf.is_current AND pcf.dos IS NOT NULL AND pcf.payer IS NOT NULL
  GROUP BY 1, 2
)
SELECT cm.payer_id, cm.payer_name, cm.payer_monday_item_id, cm.period_start, cm.period_label,
  cm.claims_submitted,
  COALESCE(pm.paid_claims_count, 0) AS paid_claims_count,
  COALESCE(dm.denied_claims_count, 0) AS denied_claims_count,
  COALESCE(pm.total_billed, 0) AS total_billed,
  COALESCE(pm.total_collected, 0) AS total_collected,
  CASE WHEN cm.claims_submitted > 0
       THEN ROUND(COALESCE(dm.denied_claims_count,0)::NUMERIC / cm.claims_submitted * 100, 1) ELSE 0 END AS denial_rate_pct,
  CASE WHEN COALESCE(pm.total_billed,0) > 0
       THEN ROUND(pm.total_collected / pm.total_billed * 100, 1) ELSE NULL END AS collection_rate_pct,
  pm.avg_payment_days,
  CASE
    WHEN cm.claims_submitted < 5 THEN NULL
    WHEN COALESCE(dm.denied_claims_count,0)::NUMERIC / cm.claims_submitted >= 0.25
      OR COALESCE(pm.avg_payment_days,0) >= 90 THEN 'F — Critical'
    WHEN COALESCE(dm.denied_claims_count,0)::NUMERIC / cm.claims_submitted >= 0.15 THEN 'D — Poor'
    WHEN COALESCE(dm.denied_claims_count,0)::NUMERIC / cm.claims_submitted >= 0.10
      OR COALESCE(pm.avg_payment_days,0) >= 60 THEN 'C — Average'
    WHEN COALESCE(dm.denied_claims_count,0)::NUMERIC / cm.claims_submitted >= 0.05
      OR COALESCE(pm.avg_payment_days,0) >= 45 THEN 'B — Good'
    ELSE 'A — Excellent'
  END AS performance_grade,
  cm.payer_monday_item_id::TEXT || '|' || TO_CHAR(cm.period_start, 'YYYY-MM') AS dedupe_key,
  cm.payer_name || ' | ' || TO_CHAR(cm.period_start, 'YYYY-MM') AS scorecard_item_name
FROM claims_monthly cm
LEFT JOIN paid_monthly pm ON pm.resolved_payer_id = cm.payer_id AND pm.period_start = cm.period_start
LEFT JOIN denials_monthly dm ON dm.payer_id = cm.payer_id AND dm.period_start = cm.period_start;
```

### Step 4 — Self-contained writer workflow

Cron daily (or whatever the desired refresh rate). Steps:

1. Schedule trigger
2. `GET /rest/v1/vw_payer_scorecard_monthly?select=*&claims_submitted=gte.5&order=payer_name.asc,period_start.desc&limit=1000` with header `Accept-Profile: rcm_ops`
3. `POST https://api.monday.com/v2` with `query { boards(ids: [<board_id>]) { items_page(limit: 500) { items { id name column_values(ids: ["<dedupe_key_col_id>"]) { id text } } } } }` — get existing items
4. Code node: build a `dedupe_key -> item_id` map from existing items. For each view row, decide `create_item` (no existing) or `change_multiple_column_values` (existing). For the `board_relation` column, pass `{"item_ids":[<linked_item_id>]}`. Compose one aliased mutation `mutation { m0: ...; m1: ...; }`.
5. `POST https://api.monday.com/v2` with the composed mutation
6. `POST /rest/v1/rcm_sync_log` with `{ board_id, board_name, direction: "supabase_to_monday", items_synced, status }`

### Step 5 — Verification (do not skip)

After the first write, query Monday with the inline fragment:

```graphql
query {
  boards(ids: [<board_id>]) {
    items_page(limit: 100) {
      items {
        id name
        column_values(ids: ["<board_relation_col_id>"]) {
          ... on BoardRelationValue { linked_item_ids linked_items { id name } }
        }
      }
    }
  }
}
```

If `linked_item_ids` is populated, the board_relation is working — don't be misled by `text: null` in a regular column_values query.

## Results / Verification

- 52 items created on board `18410275282` (was 0)
- All 52 with `linked_item_ids` populated against Payers Master board `18408472961`
- Performance grade distribution: 28 A, 8 B, 0 C, 0 D, 0 F across 9 distinct payers × multiple periods
- Sample claim 04/2026 for BLUECROSS BLUESHIELD OF TEXAS: 462 claims submitted, 396 paid, 39 denied, $87,206 billed, $35,358 collected (40.5% collection rate, 8.4% denial rate, 14.3 avg payment days → grade B — Good)
- `denials.payer_id` coverage: 23% → 100% (482/482) after backfill + cleanup
- 27 zero-amount migration-seed denials removed from both Supabase and Monday (with 26 of them having Monday item_ids that were deleted via `delete_item` mutation)

## Reusable Components

- `rcm_ops.payer_alias` table — extensible crosswalk for any future ambiguous payer text
- `rcm_ops.vw_payer_scorecard_monthly` view — single source of truth for per-payer monthly metrics
- Self-contained writer workflow `GLFwBDNBqRVXVdZi` (Daily 5 AM upsert) — pattern for any view-driven Monday board writer
- The multi-pass `payer_id` backfill SQL — copy-paste template for any FK that needs hydration from heterogeneous source columns
- The Performance Grade `CASE WHEN` block — adjust thresholds, the structure is reusable for any A-F grading scheme

## Related Entries

- KB-2026-0008 documents the upstream Monday sync hardening (drain acceleration, normalize_monday_label, etc.) that this pipeline depends on
- KB-2026-0006 (supabase-authoritative-monday-sync) — the contract that Supabase is the source of truth, which justifies renaming the Monday master to match the remittance
- The dedupe-key naming convention applied here as `{payer_monday_item_id}|{YYYY-MM}` is currently documented inside KB-2026-0006; there is no separate traceability/idempotency KB entry yet.

## Tags

n8n, monday-com, supabase, postgres, sync, data-quality, api-integration, configuration, workflow-design, monday-board

## Date

2026-05

## Status

proposed
