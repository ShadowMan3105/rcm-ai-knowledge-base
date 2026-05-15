# Lessons Learned — Payer Scorecard pipeline & naming canonicalization

**KB**: KB-2026-0009-payer-scorecard-pipeline-and-naming-canonicalization
**Date**: 2026-05-15

> Editing rules: existing `### Mistake N` blocks are immutable. New mistakes append. Subsequent updates go in the per-mistake update block, never replace the original record.

---

## Mistakes Made

### Mistake 1: Multiple Cigna entities almost got unified when remittance text was ambiguous

- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** The Monday Payers Master had two distinct Cigna payers (CIGNA HEALTHCARE and CIGNA HEALTHSPRING) representing different contracts with different fee schedules. The remittance text in `paid_claims_final.payer` literally said only "CIGNA" (no suffix) for 403 rows. The intuitive fix — rename one of the Cigna entries to "CIGNA" — would have collapsed the two distinct contracts into the same group in queries forever after.
- **Root cause:** Confusing "name match" with "entity equivalence." Two payers with overlapping names can still be distinct contractual entities. A naming-canonicalization sweep that doesn't distinguish these will silently merge them.
- **How it was caught:** The user (Dr. Seidel) intervened when we proposed the rename: "Son dos tipos de cigna. No es el mismo cigna." He pointed out the contracts differ and we had to preserve the distinction.
- **Fix applied:** Created `rcm_ops.payer_alias` — a crosswalk table where ambiguous text maps to a default payer UUID but the other entity is untouched. A `COALESCE(exact_payer_name_match, alias_lookup)` pattern in views and triggers resolves both cases without merging. The default decision is documented in the alias `notes` column for future auditors.
- **Rule extracted:** Before renaming any reference data ("the payer master", "the practice list", etc.) to match a derivative text, **count how many master entries would collapse into the same name**. If more than one would, the answer is an alias table, not a rename.
- **Subsequent Updates:** *(append-only)*
  <!-- - YYYY-MM-DD by <agent-id>: <change in the world; original Mistake stands> -->

### Mistake 2: Wasted a full minute thinking the board_relation mutation failed when it actually worked

- **Category:** `api-integration`
- **Severity:** `low`
- **What happened:** After writing 52 items to the Payer Scorecard board, the standard verification query `column_values(ids: ["board_relation_xxx"]) { id text value }` returned `text: null, value: null` for every single item. The conclusion was that the board_relation mutation hadn't applied. Two more mutation attempts with different JSON shapes (`{"item_ids":[...]}` vs `{"linkedPulseIds":[{"linkedPulseId":...}]}`) gave the same null response. The actual link had been set correctly all along — the only thing failing was the query.
- **Root cause:** Monday's GraphQL API returns `text` and `value` as `null` for `board_relation` columns in the standard `column_values` selection. The link data is only exposed via a typed fragment: `... on BoardRelationValue { linked_item_ids linked_items { id name } }`. The documentation mentions this but it's easy to miss in practice.
- **How it was caught:** A second mutation appeared to succeed (got back an `id`), and a query with the inline fragment surprisingly returned `linked_item_ids: ["11737429509"]` — proving the link existed.
- **Fix applied:** Use `... on BoardRelationValue { linked_item_ids linked_items { id name } }` for verification of any board_relation column. Standard `column_values { text value }` is unreliable for this column type.
- **Rule extracted:** When verifying a Monday `board_relation` write, the regular `text`/`value` selection lies. Use the inline fragment query. Add this to the verification step of any workflow that touches `board_relation` columns.
- **Subsequent Updates:**

### Mistake 3: Almost re-parsed a PDF to recover one $285 denial that was cheaper to drop

- **Category:** `process`
- **Severity:** `low`
- **What happened:** After multi-pass backfill brought `denials.payer_id` coverage from 23% to 94.7%, the remaining 27 unresolvable rows were investigated. 26 turned out to be zero-amount operational notes from a migration seed (not real denials). 1 was a real $285 denial whose parser had truncated the insurance name to `"PAY"`. The instinct was to re-parse the Premier Medical PDF to recover that one row — a 30-60 minute project.
- **Root cause:** Over-investing in completeness when the marginal value is tiny relative to the effort. One $285 denial in a $2M+ pipeline doesn't move any metric the scorecard reports.
- **How it was caught:** The user (Dr. Seidel) said "elimina los 27. No vale la pena por uno reparsear."
- **Fix applied:** Deleted all 27 (in both Supabase and Monday) and moved on.
- **Rule extracted:** Before re-parsing, OCR, or any large-effort recovery for a tiny number of rows, **state the dollar exposure**. If it's a rounding error on the overall total, drop it. If it's material, do the work. The threshold here is operational, not a hard rule, but stating the number forces the right tradeoff.
- **Subsequent Updates:**

### Mistake 4: Migration-seed rows in `public.denials` were operational notes ($0 denied), not real denials

- **Category:** `schema`
- **Severity:** `medium`
- **What happened:** 27 of the 509 rows in `public.denials` had `denied_amount = 0.00`, no `claim_id` link, no `source_file`, and free-text `denial_reason` fields containing handwritten notes like "ElviraE 01/28/2026 patient inactive, provider notified by email". These were created by the staff as workflow tracking cards on Monday Denials Tracker, then migrated into Supabase as if they were denials. They polluted the denial_rate metric.
- **Root cause:** The Monday Denials Tracker board doubles as a denial register AND as a follow-up workflow tool. Cards created for the second purpose got swept into Supabase by the migration without distinguishing them from real denials. The schema didn't have a `denial_type` or `is_workflow_note` flag to separate the two.
- **How it was caught:** During the backfill, these rows resisted all payer_id resolution attempts because they had no source data. Inspection revealed `denied_amount = 0.00` across all 27 — pattern too clean to be coincidence.
- **Fix applied:** Deleted them in both stores. Future detector: if a denial has `denied_amount = 0 AND denial_reason !~ '^[A-Z]{2,3}-[0-9]+'` (no proper CARC code), treat it as a workflow note candidate for review.
- **Rule extracted:** A denial register table should require `denied_amount > 0` (or be paired with a `note_type` flag). Mixing real denials with operational notes in the same table corrupts every rate calculation that uses the table.
- **Subsequent Updates:**

### Mistake 5: A view that aggregated from `parsed_claim_rows` would over-count Cigna by 4× — saved by validating against the source of truth

- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** While building the `paid_monthly` CTE for the scorecard view, the initial draft summed `paid_amount` directly from `parsed_claim_rows` (which has known duplicate rows — documented in KB-2026-0008 Mistake 5). For Cigna, this would have reported `total_collected` 4× the reality. The mistake was avoided because the design called for joining to `paid_claims_final.payer_name` and using `paid_claims_final.paid_amount` (the deduplicated source of truth) instead.
- **Root cause:** Pattern recognition — KB-2026-0008 Mistake 5 had already taught us that `parsed_claim_rows` is not deduplication-safe. Without that prior lesson, the view would have shipped with 4× inflation on at least one payer.
- **How it was caught:** Pre-emptively, by reading the previous KB entries during the design phase.
- **Fix applied:** The scorecard view's `paid_monthly` CTE aggregates from `rcm_ops.paid_claims_final` (the deduplicated final table), not from `parsed_claim_rows`. Numbers verified against direct queries.
- **Rule extracted:** **Always aggregate from the dedup-final table, never from the raw parse table.** If you have to use the raw parse for a column the final table doesn't have, `SELECT DISTINCT` on every identifier column before aggregating, and validate the aggregate against a known-good source.
- **Subsequent Updates:**

### Mistake 6: A self-contained workflow was the right choice over a generic drain queue for a view-driven board

- **Category:** `strategy`
- **Severity:** `low`
- **What happened:** The team's drain queue pattern (KB-2026-0008) handles N tables → 1 Monday board sync elegantly. The first instinct for the Payer Scorecard was to add `vw_payer_scorecard_monthly` to the drain. But the scorecard view doesn't have stable Monday item_ids that the drain assumes — the workflow has to *create* items on first run and *update* them on subsequent runs. The drain's `change_multiple_column_values` is update-only.
- **Root cause:** Conflating "everything that writes to Monday" with one architectural pattern. The drain works for entity tables where rows are pre-created in Monday and only column values change. A view-driven board where every row is "ours to create" needs a different pattern.
- **How it was caught:** During workflow design — the drain's `Fetch Pending Queue` would have nothing to consume because there's no `monday_sync_queue` trigger for a view, and the items don't exist in Monday yet.
- **Fix applied:** A dedicated workflow `GLFwBDNBqRVXVdZi cron_payer_scorecard_monthly`: fetch view + fetch existing items + Code node decides create-vs-update by `dedupe_key` lookup + single aliased mutation + log to `rcm_sync_log`. Idempotent by dedupe_key. Doesn't touch `monday_sync_queue`.
- **Rule extracted:** Two patterns. (a) **Entity-table sync**: rows already exist in Monday, push column updates only — use the generic drain queue. (b) **View-driven board sync**: workflow owns row lifecycle (create + update + maybe delete), use a self-contained workflow with `dedupe_key` upsert. Don't force pattern (a) onto a (b) problem.
- **Subsequent Updates:**

<!-- Add as many as needed. Never renumber existing mistakes. -->

---

## Assumptions That Were Wrong

- **Assumed**: `public.denials` rows all represent contractual denials with real amounts. **Reality**: 27 of them were migration-seed operational notes with $0.00 denied.
- **Assumed**: A standard `column_values { text value }` query is sufficient to verify any Monday mutation. **Reality**: `board_relation` columns return null in that selection — needs typed inline fragment.
- **Assumed**: If two payers in the master have similar-looking names, one is a duplicate. **Reality**: They can be distinct contractual entities (CIGNA HEALTHCARE vs CIGNA HEALTHSPRING) and renaming would corrupt every per-contract analysis.
- **Assumed**: The Monday master is the source of truth for the payer's canonical name. **Reality**: The ERA/PDF is canonical — the master should be renamed to match what the payer literally calls itself in the remittance.

## What to Do Differently Next Time

1. **Before any naming sweep**, query "how many master rows have a name that would collide into the same final string?" If >0, design an alias table.
2. **Verify any `board_relation` mutation** with the inline-fragment query, not the default `text/value` selection. Add this to the workflow's smoke test, not just the manual verification.
3. **Tag operational-only rows** at insert time (e.g., `is_workflow_note BOOLEAN DEFAULT false`) so they're trivially filterable later. Don't let them mix freely with accounting rows.
4. **State dollar exposure** explicitly before any large-effort recovery (re-parse, OCR, manual entry). One line: "this would recover $X across N rows."
5. **When designing a new view-driven Monday board**, default to a self-contained workflow with `Dedupe Key` upsert. Reach for the generic drain only if the board's rows truly are owned by an entity table.

## Warnings for Future AI Agents

- **Do not rename `payers.payer_name` unless you've confirmed**: (a) only one master row collapses to the new name, AND (b) the renamed payer's `monday_item_id` is preserved (downstream boards reference it). Use the `change_simple_column_value` mutation in Monday — never `delete_item` + `create_item`, that breaks every board_relation pointing at it.
- **Always include `rcm_ops.payer_alias`** in any payer-name-to-id resolution: `COALESCE(direct_match_in_payers, alias_match)`. Skipping it means CIGNA-suffix-less and any future ambiguous text fails to resolve.
- **Monday `board_relation` API quirk**: the mutation accepts `{"item_ids":[<id>]}` and returns success. The link IS set. To verify, query with `... on BoardRelationValue { linked_item_ids }` — never trust `text/value: null` from the standard column_values query for this column type.
- **The Payer Scorecard view filters `claims_submitted >= 5` before grading** — payers with fewer claims in a period have `performance_grade = NULL` (insufficient volume). Don't lower this threshold without a sample-size argument.
- **`scorecard_item_name` format is `<payer_name> | <YYYY-MM>`** — if you change this, every workflow that looks up scorecard items by name breaks. The Dedupe Key (`<payer_monday_item_id>|<YYYY-MM>`) is the stable join key; the name is for humans.
