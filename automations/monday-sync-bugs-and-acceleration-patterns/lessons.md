# Lessons Learned — Monday↔Supabase sync hardening

**KB**: KB-2026-0008-monday-sync-bugs-and-acceleration-patterns
**Date**: 2026-05-15

> Editing rules: existing `### Mistake N` blocks are immutable. New mistakes append. Subsequent updates go in the per-mistake update block, never replace the original record.

---

## Mistakes Made

### Mistake 1: n8n URL hardcoded as `localhost:5678` in 4 workflows when Docker exposes 5800

- **Category:** `configuration`
- **Severity:** `high`
- **What happened:** A monitor workflow (`cron_n8n_workflow_health_monitor`) and three statistical monitors (`cron_pending_claim_statistical_monitor`, `cron_denial_statistical_monitor`, `cron_paid_claim_statistical_monitor`) had `http://localhost:5678` baked into HTTP Request nodes. With `alwaysOutputData: true` and no guard, the failing fetches returned `{}` silently and downstream `Code` nodes interpreted the empty response as "0 executions / 0 history rows." The monitor sent "0 failures detected" to Slack every 30 minutes for an unknown duration; the statistical monitors compared current values against an empty history, never alerting.
- **Root cause:** Workflows were authored against the n8n default port (5678) while the Docker compose mapped the service to host port 5800. There is no port-discovery step at workflow runtime.
- **How it was caught:** During an audit of 33 active workflows in session 10. A `curl http://localhost:5678 ; curl http://localhost:5800` from the host confirmed only 5800 responds.
- **Fix applied:** A reusable Python script (`fix_n8n_url_5678.py`) replaces `5678` with `5800` in every HTTP node URL and PUTs the workflow back via REST. Plus a hygiene rule: every HTTP node calling the n8n internal API must read `localhost:5800`.
- **Rule extracted:** Never trust default-port assumptions in workflow JSON. Before publishing a workflow that calls the n8n internal API, `curl` the exact URL from a shell first. For any HTTP node, set `alwaysOutputData: true` ONLY if there's an `IF` node downstream that verifies the response structure (`$json.data?.boards?.[0]` or `$json.results?.length`).
- **Subsequent Updates:** *(append-only)*
  <!-- - YYYY-MM-DD by <agent-id>: <what changed> -->

### Mistake 2: JWT tokens (Monday + Supabase service_role) hardcoded in workflow header parameters

- **Category:** `security`
- **Severity:** `high`
- **What happened:** Multiple workflows had `Authorization: eyJ...` JWT tokens embedded directly in the `headerParameters` array of HTTP Request nodes. Workflow exports therefore contained the live tokens; commits to source control, paste into chat, or any export would leak them. Token rotation would require editing every workflow.
- **Root cause:** When workflows are auto-generated or copy-pasted from blueprints, the path of least resistance is to inline the token. n8n's credential system exists precisely to avoid this but requires an explicit one-time setup.
- **How it was caught:** Session-10 audit found `tQl2JRJDRw88gON6` (Payers Master Weekly Audit) with full JWT in plaintext. Subsequent sweep identified 4 more workflows with the same pattern across Monday and Supabase API calls.
- **Fix applied:** `fix_tql2_jwt_to_credential.py` converts each node to use `authentication: 'genericCredentialType' + nodeCredentialType: 'httpHeaderAuth'` and references an existing credential by ID. The token in the credential is encrypted at rest by n8n. Curator (Dr. Seidel) decided **not** to retro-fix every working workflow (the credential rotation isn't due) but to apply the template whenever a workflow is touched for another reason.
- **Rule extracted:** Never embed bearer tokens in node parameters. Always use n8n credentials. Audit existing workflows for `eyJ` (JWT prefix) or `Bearer` substrings periodically.
- **Subsequent Updates:**

### Mistake 3: `alwaysOutputData: true` without a downstream guard silently passes empty objects

- **Category:** `api-integration`
- **Severity:** `medium`
- **What happened:** Several digest/alert workflows (`cron_billing_alerts_digest`, `cron_pending_claims_stale`, `cron_appeals_due_alert`) used `alwaysOutputData: true` so the workflow wouldn't halt on a fetch error. The downstream JS would compute counts from `data.boards[0].items_page.items` and treat `undefined` as `[]`, generating "0 alerts today" Slack messages even when the upstream API actually failed.
- **Root cause:** `alwaysOutputData` is needed for clean cron chains, but it has to be paired with a structural check on the response. The first version of these workflows skipped that check.
- **How it was caught:** Audit, by pattern-matching `alwaysOutputData=true` against the presence/absence of an `IF` node downstream.
- **Fix applied:** Added an `IF` node post-fetch checking `$json.data?.boards?.[0]?.items_page?.items != null`. Branch FALSE sends a `:warning: fetch_failed` Slack alert. Branch TRUE continues. This makes silent failures impossible.
- **Rule extracted:** `alwaysOutputData: true` is a contract: the next node must verify the expected shape. If you can't verify the shape, don't use `alwaysOutputData`.
- **Subsequent Updates:**

### Mistake 4: PostgREST silently truncates queries at `max_rows=1000` without warning

- **Category:** `api-integration`
- **Severity:** `high`
- **What happened:** The daily-snapshot workflow (`PmHcbQTUVfLQWPWb`) did `GET /rest/v1/payments?limit=5000` then computed `data.length` to get the total payment count. PostgREST silently capped the response at 1,000 rows. The metric `total_payments` was reported as `1000` when the real value was 9,115. `total_paid_amount` was about 10× under-reported. The Daily Snapshot wrote wrong numbers to `rcm_daily_snapshots` for an unknown number of days.
- **Root cause:** PostgREST has a server-side `max-rows` setting (default 1000) that applies regardless of the URL `limit` parameter. The truncation is silent — the response has no header indicating truncation unless you ask for `Prefer: count=exact`.
- **How it was caught:** A discrepancy between the snapshot's `total_paid_amount` and a manual `SELECT SUM(amount) FROM payments` query was noticed during a separate audit.
- **Fix applied:** Replaced the four `GET` calls + JS aggregation with a single SQL RPC function `public.compute_daily_snapshot_metrics()` that returns a `JSONB` with all the counts/sums via Postgres aggregation. Server-side, no row transfer, no truncation. The workflow simplified to 3 nodes.
- **Rule extracted:** **Never compute counts or sums in a workflow by fetching rows + reducing.** Always use an RPC SQL function that returns the aggregate directly. If you must fetch rows, use `Prefer: count=exact` plus `Content-Range` header parsing to detect truncation and paginate with `Range`.
- **Subsequent Updates:**

### Mistake 5: `rcm_audit.parsed_claim_rows` contains duplicate service-line rows; `SUM(provider_paid)` double-counts

- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** While building the partial-payment audit (`claim_partial_pay_audit`), an early RPC version reported `total_paid = $295.76` for claim 180811 while `paid_claims_final.paid_amount` was `$147.88` (exactly half). Three CPT lines were appearing twice each in `parsed_claim_rows`. `jsonb_agg(DISTINCT ...)` deduplicated the array shown to the user, but the parallel `SUM(provider_paid)` didn't, producing an internally inconsistent row.
- **Root cause:** The PDF parser writes the same `(claim_number, dos, cpt_code, modifier, billed, provider_paid)` tuple twice in some cases (origin uninvestigated). Aggregating over the raw table without de-duping yields inflated sums.
- **How it was caught:** Visual inspection of a generated `audit_breakdown` text — the displayed CPTs summed to a different number than the displayed total.
- **Fix applied:** Pre-deduplicate in a CTE `lines_unique AS (SELECT DISTINCT claim_number, dos, report_type, cpt_code, modifier_1, provider_paid, billed, denial_code FROM parsed_claim_rows WHERE row_type='service_line' AND cpt_code NOT LIKE '%,%')` before any aggregation. Plus a validation gate: the RPC only inserts a row when `ABS(total_paid_computed - paid_claims_final.paid_amount) < 0.51`. If the gate fails, the row is silently dropped from the audit instead of propagating wrong data to Monday.
- **Rule extracted:** When aggregating over a table whose row-uniqueness isn't guaranteed, **always `SELECT DISTINCT` the dimension columns first**, then aggregate. **Always validate the computed aggregate against a known-good source-of-truth before persisting** (in this case, against `paid_claims_final.paid_amount`).
- **Subsequent Updates:**

### Mistake 6: Monday `change_multiple_column_values` aliased mutation rejects the WHOLE batch when one item is archived

- **Category:** `api-integration`
- **Severity:** `medium`
- **What happened:** The drain workflow batches 50 items per mutation using aliases (`c0:`, `c1:`, ..., `c49:`). When one item's `monday_item_id` pointed to an archived (`state: archived`) item, Monday returned `"Cannot change column value for inactive items"` with `inactive_pulse_ids: [<X>]` and rejected the entire mutation. 50 active items per cycle got marked as failed because of 1 archived sibling.
- **Root cause:** The aliased-mutation API doesn't isolate failures per alias. Monday API semantics: the GraphQL mutation either succeeds in full or fails. The error data identifies the offender, but the other aliases don't run.
- **How it was caught:** 7 paid_claims_final entries stuck in `status=error` with the same `inactive_pulse_ids` value across all of them.
- **Fix applied (workaround):** Marked the 7 entries as `error` with `retry_count=3` and a clear message `'Item archived in Monday — audit_breakdown sync skipped'`. They no longer block live items.
- **Rule extracted:** Before sending an aliased bulk mutation to Monday with N>5 items, ideally pre-flight a `query { items(ids: [...]) { id state } }` and exclude items where `state != "active"`. Until that's implemented, **archived items must be detected eagerly** (e.g., by a webhook or a periodic check) so their `monday_item_id` in Supabase can be set to NULL before they reach the queue.
- **Subsequent Updates:**

### Mistake 7: Drain `priority` field defaulted to NULL caused `ORDER BY priority DESC` to put NULLs first, blocking the bumped items

- **Category:** `schema`
- **Severity:** `medium`
- **What happened:** During the drain acceleration, 245 entries were re-prioritized with `priority=100` so they'd jump the 17k-item FIFO queue. The drain workflow's fetch query was `ORDER BY priority.desc, created_at.asc`. With the other 18k rows having `priority=NULL`, PostgreSQL's default `NULLS FIRST` semantic put the NULL-priority items at the top of the DESC sort — the priority-100 items never appeared in the fetched batch.
- **Root cause:** `ORDER BY ... DESC` in PostgreSQL defaults to `NULLS FIRST`. Combined with a column where most rows are NULL, any priority bump is invisible.
- **How it was caught:** After bumping priorities, the drain processed 193 items in the next cycle but none of them were the priority-100 ones.
- **Fix applied:** Set the column's default to `5` (a middle priority) and backfilled all existing NULLs to `5`. Then `priority=100` items naturally rose to the top. Also documented `NULLS LAST` explicit in the fetch URL where supported.
- **Rule extracted:** When using a `priority` column for queue ordering, **never allow NULL values**. Set `DEFAULT <int>` and `NOT NULL` from the start, or backfill at creation time. Don't rely on default sort semantics across databases.
- **Subsequent Updates:**

### Mistake 8: Monday dropdown/status labels are case-sensitive; Supabase sent lowercase/snake_case values

- **Category:** `api-integration`
- **Severity:** `medium`
- **What happened:** The `denials.denial_category` Postgres column stored values like `eligibility`, `other`, `coding_error`. Monday's `Denial Category` dropdown column had labels `Eligibility`, `Other`, `Coding`, etc. Sending `eligibility` to the Monday API returned `"The dropdown label 'eligibility' does not exist, possible labels are: {...}"`. Similarly, `claims.status='paid'` failed against a `color` column expecting `Resuelto`. 269 + 12 entries failed with this exact pattern.
- **Root cause:** Two independent normalization conventions (snake_case in Postgres, Title Case in Monday) with no translation layer between them.
- **How it was caught:** Aggregating queue errors by `error_message LIKE '%dropdown label%'` after the acceleration test.
- **Fix applied:** Added `public.normalize_monday_label(table, field, value)` as an `IMMUTABLE` SQL function with CASE WHEN clauses for the known mappings. Called from inside `queue_monday_sync()` trigger so the cv jsonb always contains the canonical Monday value. Unknown values normalize to NULL (stripped by `jsonb_strip_nulls()`), so future enum extensions don't crash the queue.
- **Rule extracted:** Every cross-system enum mapping must be **deterministic and codified in a single function**. Never let downstream consumers infer the mapping. When the source enum extends, the function returns NULL for the new value until explicitly added — fail-safe.
- **Subsequent Updates:**

### Mistake 9: The drain serializer `toMondayValue()` defaulted unknown column types to plain `String`, breaking `board_relation` columns

- **Category:** `api-integration`
- **Severity:** `medium`
- **What happened:** The drain workflow's `toMondayValue(rawValue, colType)` JS function had explicit cases for `numbers`, `date`, `color`, `status`, `dropdown`, but `board_relation` fell into the `default` case which returned `String(rawValue)` (e.g., the payer name as a plain string). Monday rejected this with `"Link to item column value structure invalid"` because `board_relation` requires `{ item_ids: [<linked_item_id>] }` or `{ linkedPulseIds: [{linkedPulseId: <id>}] }`. The payer/practice link columns silently never synced for any paid_claims_final item.
- **Root cause:** The serializer was built for the common cases and the rare ones fell through to a too-permissive default. The downstream side (Monday API) is strict; the upstream side (JS switch) was lax.
- **How it was caught:** When auditing failed queue entries by `error_message LIKE '%board-relation%'`.
- **Fix applied:** Until a `name → monday_item_id` lookup table exists (D3 in the roadmap), the trigger `queue_monday_sync()` now **strips** `payer` and `practice` from the paid_claims_final cv entirely. They're never sent. The Monday board's existing links remain untouched (they were populated at item creation by a different workflow).
- **Rule extracted:** Don't send fields you can't serialize. The trigger that fills the queue is the right place to gate "what gets sent" — the workflow is too late. When the serializer doesn't have a case for a column type, omit the field rather than guess.
- **Subsequent Updates:**

### Mistake 10: n8n DataTable size limit is INSTANCE-WIDE (sum across all tables), not per-table

- **Category:** `configuration`
- **Severity:** `high`
- **What happened:** Multiple cache DataTables in n8n (`monday_board_cache_v2`, `denials_cache_v2`, `paid_claims_cache_v1`, `pending_claims_cache_v1`, ...) all share a single instance-wide budget set by `N8N_DATA_TABLES_MAX_SIZE_BYTES` (default 50 MB). When a cache refresh failed mid-write due to size exhaustion, the failure mode was an n8n DataTable validation error that **escaped the try/catch** in the workflow node and left an orphaned execution.
- **Root cause:** The DataTable system is convenient for "a small lookup table inside n8n" but doesn't scale per-table; the limit is shared. Workflow authors assumed each table had its own quota.
- **How it was caught:** A workflow execution hanging in "running" forever; investigation showed a 50MB error in the DataTable insert.
- **Fix applied:** Bumped the env var: `N8N_DATA_TABLES_MAX_SIZE_BYTES=524288000` (500MB), `N8N_DATA_TABLES_WARNING_THRESHOLD_BYTES=419430400` (400MB warning). Plus a cleanup: deleted 10,685 stale rows from `monday_board_cache_v2` (~34 MB → 2.5 MB) and VACUUM FULL. Planned: D4 migrates the largest table out of DataTables entirely into Supabase Postgres.
- **Rule extracted:** **n8n DataTables are not a substitute for a real database table when the data volume is unbounded.** Use them for small lookups (<1 MB), config flags, or transient caches that you can `truncate` daily. For anything that grows with business volume, use Postgres (Supabase) and access via PostgREST or RPC.
- **Subsequent Updates:**

<!-- Add as many as needed. Never renumber existing mistakes. -->

---

## Assumptions That Were Wrong

- **Assumed**: n8n DataTable size limit is per-table. **Reality**: it's instance-wide sum.
- **Assumed**: PostgREST `limit=5000` would return up to 5000 rows. **Reality**: server cap at 1000, silently.
- **Assumed**: `parsed_claim_rows` has one row per service line per claim. **Reality**: some lines duplicate.
- **Assumed**: Monday accepts plain strings for any column type when sent as a value. **Reality**: `board_relation`, `dropdown`, `status`, `long_text` all have specific JSON shapes; only `text`/`name` accept raw strings.
- **Assumed**: `alwaysOutputData: true` is a safe knob to keep cron workflows from breaking. **Reality**: it's a contract that requires a downstream shape check.
- **Assumed**: A monitor that "checks recent executions" is fine if the URL is `localhost:5678`. **Reality**: Docker mapping changed the host port; the monitor was sending empty reports for an unknown duration.

## What to Do Differently Next Time

1. **Before publishing any workflow that hits the n8n internal API**, run `curl -I http://localhost:<port>/api/v1/executions` from the host to confirm port + auth. Add a sticky note on the canvas with the confirmed URL.
2. **When mapping a Postgres column to a Monday dropdown/status column**, immediately add the lowercase→Title-Case mapping to `public.normalize_monday_label()`. Don't wait for the first sync failure.
3. **For any new SQL aggregation RPC**, validate the result against an independent source-of-truth (e.g., `paid_claims_final.paid_amount` for breakdowns) and gate the persistence on the validation.
4. **For any new DataTable**, estimate the max row count × max bytes/row and confirm `total_DataTables_size < N8N_DATA_TABLES_MAX_SIZE_BYTES / 2` (leave 50% headroom).
5. **For any new aliased Monday mutation**, plan the pre-flight item-state check from day 1, even if you skip implementing it initially. Don't let archived items become a silent bottleneck.
6. **Set `priority NOT NULL DEFAULT <int>`** on any queue column that participates in `ORDER BY`. Never allow NULL.

## Warnings for Future AI Agents

- **The drain workflow's `toMondayValue()` switch in JS does NOT handle `board_relation`.** If a column mapping is added in `monday_column_map` with `monday_col_type='board_relation'`, the workflow will silently fail to apply that field. The fix is in `queue_monday_sync()` (SQL trigger) — strip the field from the cv there. Adding a JS case for `board_relation` requires a `name → monday_item_id` lookup table which doesn't exist yet.
- **`public.normalize_monday_label()` is the only place to add new dropdown/status mappings.** Don't fork it in JS. Don't bypass it by adding raw cv fields in `queue_monday_sync()` without wrapping. The function is `IMMUTABLE` so it's safe to inline in views.
- **`parsed_claim_rows.row_type='service_line'` is NOT a primary key.** Always `SELECT DISTINCT` before aggregating. Filter `cpt_code NOT LIKE '%,%'` to exclude summary rows that have comma-joined CPT codes.
- **`monday_sync_queue.priority` defaults to 5 in current schema.** If you bump a row to `priority=100`, it WILL be picked first IF the rest of the queue is at 5 or below. But if you re-insert a row via a trigger that omits `priority`, the new row gets `5` (not NULL). Don't worry about NULLS FIRST anymore in this table.
- **DataTable size is global.** Before adding a new cache, check current usage in the n8n UI (Settings → Data Tables). If you're near 80% of `N8N_DATA_TABLES_MAX_SIZE_BYTES`, use Postgres instead.
- **n8n is on `localhost:5800`, NOT 5678.** Audit any new workflow's URLs with `grep '5678'` before publishing.
