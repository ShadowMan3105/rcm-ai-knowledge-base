# KB-2026-0008 — Monday↔Supabase sync hardening: bug catalog, label normalization, drain acceleration & DataTable migration design

## Summary

Three working sessions (May 14-15, 2026) hardened the Supabase→Monday sync pipeline against 10 distinct bugs uncovered by attempting a high-volume drain (22k+ queue entries) and a feature rollout (claim-level audit breakdown for partial-payment claims). The pipeline went from 63% sync success and 45-hour drain time to 99.9% success and 1.5-hour drain time, with all data integrity guarantees preserved. This entry catalogs each bug, the root-cause fix applied, and the design for the next-phase migration of the `monday_board_cache_v2` n8n DataTable to dedicated Postgres in Supabase (D4).

## Context

The Supabase→Monday sync runs via a queue table (`public.monday_sync_queue`) drained every 30 min by an n8n workflow that batches mutations through the Monday GraphQL API. Both sides accumulate edits asynchronously; the queue plus a `last_modified_by` anti-loop guard keeps the system convergent.

Two pressures exposed latent bugs simultaneously:

1. **Feature rollout (audit_breakdown)**: A new column (`long_text Desglose Auditoría`) added to two Monday boards required propagating a computed text field from Supabase. 245 fresh queue entries surfaced existing serialization bugs the moment the drain tried to push them.

2. **Backlog drain (20,485 entries)**: The drain inherited from a prior session ran for days because limit/interval were tuned for normal load, not catch-up. Accelerating the drain magnified pre-existing per-item failures.

The pipeline runs on:
- **n8n** in Docker on `localhost:5800` (NOT default 5678 — a recurring trap)
- **Supabase Cloud** project `fjqajxfuuxjlcmlyocpq` with schemas `public`, `rcm_ops`, `rcm_audit`
- **Monday.com** workspace 15028662, multiple boards (paid claims, denials, claims, AR, payers, practices)

## Approach / Strategy

The fixes fall into 4 thematic groups, applied in the order:

### Group 1 — Source-of-truth normalization (root cause: serializer too permissive)

Monday rejects values that don't match exact column constraints. The drain workflow's `toMondayValue()` switch-case in JS defaulted unknown column types to a plain string. For `dropdown` and `status (color)` columns Monday expects an object `{ label: "<exact text>" }` and the label must match the configured enum **case-sensitively**.

The fix is to **normalize at the SQL trigger** that fills the queue (`queue_monday_sync()`), not at the JS workflow:

```sql
CREATE FUNCTION public.normalize_monday_label(
  p_table_name TEXT, p_field_name TEXT, p_raw_value TEXT
) RETURNS TEXT LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
  IF p_table_name = 'denials' AND p_field_name = 'denial_category' THEN
    RETURN CASE LOWER(p_raw_value)
      WHEN 'authorization' THEN 'Authorization'
      WHEN 'eligibility'   THEN 'Eligibility'
      WHEN 'coding_error'  THEN 'Coding'
      WHEN 'other'         THEN 'Other'
      -- ...
      ELSE NULL  -- unknown → strip instead of send-and-fail
    END;
  END IF;
  -- claims.status (paid → Resuelto, denied → Stuck, pending → Pendiente)
  -- ...
  RETURN p_raw_value;
END $$;
```

The trigger then wraps every dropdown/status read with this function:

```sql
'denial_category', public.normalize_monday_label('denials','denial_category', v_row ->> 'denial_category')
```

**Why at the trigger, not the workflow JS:** SQL is deterministic and testable; the workflow JS is harder to version-control and lives in n8n. The normalization map is one place to update.

### Group 2 — Workflow misconfigurations (wrong URL, leaked credentials)

A grep across active workflows found:
- **4 workflows** hardcoded `http://localhost:5678` (n8n default) but Docker runs on `5800`. With `alwaysOutputData=true` and no guard, fetch failures silently returned `{}` and the code interpreted as "0 results."
- **2 workflows** had JWT tokens (Monday API, Supabase service_role) embedded in header `parameters` rather than referenced via `credentialId`. Token rotation would be a footgun; secrets were in workflow JSON exports.

Both fixed by Python scripts that PUT the corrected workflow back via n8n REST API:
- `fix_n8n_url_5678.py` — string replace `5678` → `5800` in HTTP node URLs
- `fix_tql2_jwt_to_credential.py` — convert `Authorization: <jwt>` header to `authentication: genericCredentialType + httpHeaderAuth` referencing an existing credential

### Group 3 — Aggregation correctness in Postgres (duplicates + max_rows)

Two data-quality traps:

1. **`rcm_audit.parsed_claim_rows` has duplicate service-line rows.** The PDF parser writes the same CPT+amount twice for some files. A SUM over `provider_paid` double-counts; `jsonb_agg(DISTINCT ...)` collapses the array but the SUM doesn't. The fix: pre-deduplicate in a CTE before aggregating.
   ```sql
   WITH lines_unique AS (
     SELECT DISTINCT claim_number, dos, report_type, cpt_code, modifier_1,
                     COALESCE(provider_paid, 0) AS provider_paid, billed, denial_code
     FROM rcm_audit.parsed_claim_rows
     WHERE row_type='service_line' AND cpt_code NOT LIKE '%,%'  -- exclude summary rows
   ),
   mixed AS (
     SELECT claim_number, dos, SUM(provider_paid) FILTER (WHERE report_type='PAID' AND provider_paid > 0) AS total_paid
     FROM lines_unique GROUP BY claim_number, dos
   )
   ```
   Plus a validation gate: only persist a row when `total_paid_calculated ≈ paid_claims_final.paid_amount` (±$0.51). If it doesn't match, the breakdown is silently dropped instead of polluting Monday with wrong numbers.

2. **PostgREST `max-rows = 1000` server-side cap.** Any GET with `limit > 1000` is silently truncated. Workflows that did `?limit=5000` and then `data.length` got "5,000 payments" when reality was 9,115. Fix: use an RPC SQL function that returns aggregates as JSONB.
   ```sql
   CREATE FUNCTION public.compute_daily_snapshot_metrics()
   RETURNS JSONB LANGUAGE sql STABLE AS $$
     SELECT jsonb_build_object('total_payments', (SELECT COUNT(*) FROM payments), ...)
   $$;
   ```

### Group 4 — Drain acceleration with bounded blast radius

The drain v2 ran at `limit=200` per cycle, `cron */30 min` = 400 items/hr. For a 17k backlog this was 45 hours.

The acceleration math:
- **Monday API budget**: 5,000 complexity points/min/key. `change_multiple_column_values` ~ 10-15 points/value × 5 values/item × 50 items/mutation × 20 mutations/cycle = ~750 points/cycle.
- **PostgREST cap**: 1,000 rows/fetch.
- **n8n Docker timeout**: default 5 min per execution.

So the safe upper bound for a single cycle is **1,000 items in ~3 min** (50 mutations of 20 items each, each ~3s). Cron `*/5 min` gives a 2-min margin between executions. **12,000 items/hr**, drain in ~1.5 hr — 30× improvement.

Caveats baked in:
- After acceleration, **revert** to normal (200/30min) when backlog clears, to leave headroom for Monday API spikes.
- **Priority field** on the queue lets surgical bumps (e.g., re-queue specific items) pre-empt the natural FIFO order. PostgreSQL `ORDER BY priority DESC` puts NULLs first — set explicit `priority=0` defaults to avoid this.
- **Bulk mutation contagion**: Monday `change_multiple_column_values` with aliases — if ONE item is archived (`inactive_pulse_ids`), the WHOLE mutation rejects. The 7 archived items in the queue blocked 50-item batches until they were marked `status='error'` with retry_count=3 and skipped permanently.

### Group 5 — D4 design (DataTable → Postgres dedicated)

**Current state**: `monday_board_cache_v2` lives as an n8n DataTable. Limits:
- Global instance cap (now 500 MB across ALL DataTables, was 50 MB default — env var `N8N_DATA_TABLES_MAX_SIZE_BYTES`)
- Filter API is AND-only with `eq`/`lt` operators. No `OR`, `IN`, `LIKE`.
- No joins with the business data in Supabase
- No native indexes, no EXPLAIN, no concurrent-safe writes

**Target**: a regular table `rcm_ops.monday_board_cache` in the same Supabase project, written via PostgREST `?on_conflict=cache_key` and read with arbitrary SQL.

**Zero-downtime cutover** (4 phases, ~5-6 hours total spread):

1. **Setup** (1h): `CREATE TABLE rcm_ops.monday_board_cache(...)` with index `(board_id) WHERE is_current=true` and `UNIQUE(cache_key)`. RPC functions optionally wrap the 4 operations actually used (`get-with-filter`, `mark-stale-by-board`, `upsert-by-cache-key`, `purge-by-stale-cutoff`). Zero risk — no existing workflow touched.

2. **Dual-write** (1h): Modify the writer `cron_monday_board_cache_refresh_v3_full` to do every write twice: first to the DataTable (existing path), then to Postgres via HTTP POST. **Fail-safe rule**: if Postgres write fails, log to `rcm_sync_log` and continue. NEVER rollback the DataTable write. Eventual consistency. Verify 24h: row counts match.

3. **Migrate readers one-by-one** (2.5h): For each of the 5 active readers (cache_health_alert, ar_aging_snapshot, data_retention_purge, tool_cash_dashboard, tool_claim_lookup), replace the DataTable `get` node with an HTTP Request to `https://fjqajxfuuxjlcmlyocpq.supabase.co/rest/v1/monday_board_cache?...`. Same JSON output structure, downstream code unchanged. Test each manually. Rollback = revert that one workflow; the DataTable is still being written so reverting is a 1-line change.

4. **Cutover writer** (30min) after 1 week of dual-write stability: writer stops writing to DataTable. Then **Cleanup** (30min): DROP DataTable; document the lesson.

**Risks and mitigations**:

| Risk | Mitigation |
|---|---|
| Race between two stores | DataTable first, Postgres second (eventual consistency) |
| `max-rows=1000` silently truncates a board with 7,602 items (Paid 2026) | Use `Range` header pagination or RPC SQL function |
| Permissions on Postgres table | service_role bypasses RLS; same credential already configured |
| TZ mismatch on `synced_at`/`stale_at` | Use `TIMESTAMPTZ`; DataTable also TZ-aware |
| Workflow upgrade order matters | Writer is upgraded LAST (phase 3) — until then, DataTable is the canonical write target |

**Why reuse Supabase (vs. a new Docker Postgres container or the n8n internal Postgres)**:
- Zero new infrastructure
- Joins against `paid_claims_final`/`denials`/`claims` (impossible from a DataTable)
- Backup and disaster recovery already covered
- PostgREST + service_role already wired
- ~10-20 MB additional storage absorbed by current plan

## Final Blueprint

### Standard fix for "dropdown label does not exist" errors

Whenever a Monday `dropdown` or `status` column is mapped from a Supabase enum/text field:

1. Add a clause to `public.normalize_monday_label()` for `(table_name, field_name)` mapping each lowercase/snake_case Supabase value to the exact Monday label.
2. Wrap the field with `public.normalize_monday_label(...)` inside the `queue_monday_sync()` `CASE TG_TABLE_NAME` block. Don't fix this in workflow JS — keep it in SQL.
3. Unknown values normalize to `NULL` so they're stripped via `jsonb_strip_nulls()` rather than sent and rejected. (Better strip than send-and-fail.)

### Standard fix for "Link to item column value structure invalid" (`board_relation`)

Until a `name → monday_item_id` lookup table exists for the related boards, **strip** the field from the cv at the trigger:

```sql
-- in paid_claims_final cv, OMIT 'payer' and 'practice'
v_column_values := jsonb_strip_nulls(jsonb_build_object(
  'claim_number', v_row ->> 'claim_number',
  -- 'practice' INTENTIONALLY EXCLUDED — board_relation bug
  -- 'payer' INTENTIONALLY EXCLUDED — board_relation bug
  -- ... other fields
));
```

The columns in Monday were populated when items were created; subsequent name changes won't sync, but that's acceptable for this entity (changes are rare, manual fix possible).

### Drain throughput formula

For any Monday-write workflow draining a Supabase queue:

```
items_per_hour = (fetch_limit ÷ cycle_minutes) × 60
              = constrained by:
                - Monday API: 5000 complexity / min ÷ (avg complexity per item)
                - PostgREST: 1000 rows max_rows (or use RPC + Range pagination)
                - n8n exec timeout: items × ~50ms per mutation < timeout
```

Default safe values for **accelerated catchup**: `fetch_limit=1000`, `cycle=5min`, `batch=50 per aliased mutation`. Revert to `fetch_limit=200`, `cycle=30min` once backlog clears.

Always set `priority` to a default non-NULL (e.g., 0 or 5) on the queue so `ORDER BY priority DESC` doesn't surprise you with NULL-FIRST semantics.

### Queue cv schema rule

Every entity_type clause in `queue_monday_sync()` must:
1. Use `jsonb_strip_nulls()` so NULL fields don't waste queue space and don't cause Monday to set columns to empty.
2. Pass dropdown/status values through `normalize_monday_label()`.
3. Omit `board_relation` fields (until D3 lookup tables exist).
4. Include the `audit_breakdown` field if the entity has it (paid_claims_final, denials).

### Bulk mutation pre-flight (recommended, not yet implemented as of 2026-05-15)

Before sending an aliased mutation with N items to Monday, optionally query:

```graphql
query { items(ids: [...]) { id state } }
```

Items with `state != "active"` are excluded from the mutation. This prevents the contagion where one archived item rejects 49 healthy ones in the same batch. Skipped from current sprint due to complexity vs. payoff (the 7 archived items have been quarantined manually).

## Results / Verification

### Drain acceleration measured

- **Baseline** (drain v2, `limit=200`, `cron=30min`): 200 items / 30 min = 6.7 items/min = 400 items/hr → 45 hr for 18k backlog
- **Accelerated** (drain v3, `limit=1000`, `cron=5min`, `batch=50`): observed 295 items/min in burst, sustained ~200 items/min = 12,000 items/hr → 1.5 hr for 18k backlog
- **Bug-fixed sustained**: 886 processed / 1 transient retry in a 3-min cycle = **99.9% success** (vs. 63% before fixes)

### `audit_breakdown` rollout

- 125 claims with mixed-CPT status (some paid, some denied within same claim+DOS) detected
- 125/125 row totals match `paid_claims_final.paid_amount` exactly (validation gate)
- 238/245 queue entries synced to Monday (97%); the 7 remaining were Monday-archived items quarantined

### Cleanup gains

- Supabase DB size: 192 MB → 158 MB (34 MB freed by `DROP SCHEMA rcm_backup CASCADE` + index pruning + `VACUUM ANALYZE` × 7 tables)
- 16 unused/duplicate indexes dropped
- DataTable `monday_board_cache_v2` reclaimed from 34 MB → 2.5 MB after `DELETE WHERE is_current=false AND stale_at < NOW() - INTERVAL '90 days'` and VACUUM

### Statistical monitor reactivation

3 cron workflows (`cron_pending_claim_statistical_monitor`, `cron_denial_statistical_monitor`, `cron_paid_claim_statistical_monitor`) had been silently broken for an unknown period due to `localhost:5678` hardcoded URL. After the `5678 → 5800` fix:
- Workflows now query the snapshot history correctly.
- Spam Slack branch ("Notify Paid Trend Normal") removed from `cron_paid_claim_statistical_monitor` — was sending a daily "everything ok" message regardless of alert state.

## Reusable Components

The following Python scripts in `scripts/` are reusable across future workflow maintenance:

| Script | Purpose |
|---|---|
| `fix_n8n_url_5678.py` | Bulk replace `localhost:5678` → `localhost:5800` in n8n workflow nodes via REST API |
| `fix_tql2_jwt_to_credential.py` | Template: convert hardcoded JWT header to `httpHeaderAuth` credential reference |
| `n8n_put_workflow.py` | Round-trip workflow via REST (GET → modify → PUT) preserving settings |
| `add_digest_fetch_guard.py` | Insert an IF node post-fetch that aborts the workflow if `data.boards?.[0]?.items_page` is missing |
| `revert_drain_to_normal.py` | After accelerated drain, restore `limit=200` and `cron=30min` |
| `apply_c3_m1_indexes.py` | Idempotent indexes + cache repointing + Slack string fix |
| `build_cache_refresh_v3_full.py` | Builds the full v3 paginated cache writer from scratch |

SQL artifacts:

- `public.normalize_monday_label(p_table, p_field, p_raw)` — IMMUTABLE function, lookup-table replacement at SQL level
- `public.compute_daily_snapshot_metrics()` — JSONB-returning RPC that bypasses `max_rows` via SQL aggregation
- `rcm_ops.claim_partial_pay_audit` table with validation gate (only inserts rows where `total_paid_computed ≈ paid_claims_final.paid_amount`)
- `rcm_ops.refresh_partial_pay_audit()` and `rcm_ops.apply_partial_pay_audit()` — idempotent refresh+propagate pair
- `rcm_ops.workflow_locks` table + `acquire_lock(name, by, ttl)` / `release_lock(name, by)` RPCs — cooperative locking (created, not yet integrated)

## Related Entries

- **KB-2026-0006-supabase-authoritative-monday-sync** — original sync direction & precedence rules. This entry extends it with concrete failure modes encountered in production.
- Idempotency key conventions (`{entity}_key`, `payment_idempotency_key`, etc.) are currently documented inside **KB-2026-0006-supabase-authoritative-monday-sync**; there is no separate traceability/idempotency KB entry yet.
- **KB-2026-0007-denied-claims-refresh-cache-rebuild-strategy** — cache rebuild pattern; the D4 design here will let denied-claims cache eventually use the same Postgres approach.

## Tags

n8n, monday-com, supabase, postgres, sync, performance, data-quality, security, configuration, api-integration

## Date

2026-05

## Status

proposed
