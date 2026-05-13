# Lessons Learned - Supabase-Authoritative Monday.com Sync With Dry-Run Ledger And Hold Gates

## Mistakes Made

### Mistake 1: Treating the work board as if it were the source of truth
- **Category:** `strategy`
- **Severity:** `high`
- **What happened:** Early synchronization planning risked using Monday board state as if it could decide the canonical claim state after durable final rows already existed.
- **Root cause:** Operational convenience and durable audit authority were not separated sharply enough.
- **How it was caught:** Review of the end-to-end route clarified that parsing, normalization, dedupe, and durable final rows must complete before Monday synchronization, and that Monday is only the operational output surface.
- **Fix applied:** The sync design was constrained so Supabase final rows drive Monday creates, updates, links, skips, and holds. Monday-only manual fields can assist human workflow but cannot override canonical claim evidence.
- **Rule extracted:** Never let Monday decide claim truth after Supabase has normalized final rows. Always treat Monday as an operational sync target, not as the durable claims audit source.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 2: Planning writes before proving the board schema and item identity
- **Category:** `api-integration`
- **Severity:** `high`
- **What happened:** It was tempting to map fields by visible column names and expected board layout before proving the current Monday schema, item naming convention, relation shape, and existing item IDs.
- **Root cause:** Familiar boards can look stable while column IDs, relation-value formats, groups, and required fields drift over time.
- **How it was caught:** Read-only inspection showed that safe sync requires current board schema, column types, sample items, relation values, and existing ledger evidence before writes.
- **Fix applied:** The implementation path starts with read-only inspection and a dry-run planner. Writes are allowed only after create/update/link/skip/hold counts are known and sampled.
- **Rule extracted:** Never assume Monday column names, relation values, groups, or item identity from memory. Always read the current board schema and sample items before planning writes.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 3: Coupling Monday writes and Supabase ledger updates in one fragile step
- **Category:** `process`
- **Severity:** `high`
- **What happened:** A batch pattern that created Monday items and updated durable ledger fields in the same execution could leave the two systems temporarily out of sync if the second half failed.
- **Root cause:** A successful external write and a successful durable ledger update were treated as one atomic event even though they happen through different systems and failure modes.
- **How it was caught:** Live controlled batches showed that a Monday write can complete while a later ledger step fails or needs separate verification.
- **Fix applied:** The safer pattern became two-step: write to Monday, re-read and verify the item, then update the Supabase ledger separately with exact link operations.
- **Rule extracted:** Never mark a durable ledger row synced only because a Monday mutation returned success. Always re-read Monday first, then update the ledger in a separately verified step.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 4: Treating same claim and service date as automatic duplicate evidence
- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** Duplicate scans found records that looked duplicated by claim and service date, but many were service-line split artifacts that needed comparison against the aggregate final row before any cleanup decision.
- **Root cause:** Operational board rows and audit/service-line detail were not clearly separated during duplicate classification.
- **How it was caught:** Comparison against durable final rows showed that Monday should hold the aggregate operational representation, while service-line detail belongs in audit storage.
- **Fix applied:** Duplicate cleanup was changed to classify exact duplicates, partial duplicates, service-line split rows, wrong-board routing, amount mismatches, and missing durable evidence separately.
- **Rule extracted:** Never delete, archive, or mark duplicate claim rows from Monday based only on claim number and service date. Always compare candidates to the durable aggregate final row first.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 5: Using per-item status writes as a runner lock for large jobs
- **Category:** `process`
- **Severity:** `medium`
- **What happened:** A proposed large-run safety idea used item-level status changes to show that a bot was currently processing rows.
- **Root cause:** Business state and process-control state were being mixed into the same operational board surface.
- **How it was caught:** Large board jobs need to prevent overlap at the board/process level, not by touching every item for runner bookkeeping.
- **Fix applied:** The preferred design became a process-level lease lock with heartbeat, expiry, and checkpoint stored in durable storage or a control table.
- **Rule extracted:** Never use per-item Monday status columns as the primary lock for large automation runs. Always use a board/process-scoped lease lock with heartbeat, expiry, and checkpoint.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 6: Overwriting manual pending workflow fields during canonical sync
- **Category:** `process`
- **Severity:** `medium`
- **What happened:** Pending board records contained manual workflow fields that could be overwritten if the canonical sync treated every board field as part of the official report state.
- **Root cause:** Official report evidence and internal work-tracking fields were not separated in the update contract.
- **How it was caught:** Pending reconciliation rules showed that manual fields are useful for staff work but are not official paid or denied evidence.
- **Fix applied:** Pending updates were limited to official fields sourced from Supabase, and manual/internal fields were left untouched.
- **Rule extracted:** Never overwrite manual pending workflow fields during canonical Supabase-to-Monday sync. Always update only official report fields and use official paid or denied evidence to change pending state.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

## Assumptions That Were Wrong

The main wrong assumption was that once a record existed somewhere in Monday, the sync problem was mostly solved. In reality, the sync still had to prove the right board, right group, right item identity, right aggregate amount, right relation mapping, and right ledger link.

Another wrong assumption was that duplicate detection could run independently from the durable database. Monday-only duplicate detection can flag candidates, but final cleanup decisions require comparison against the authoritative aggregate final rows.

## What to Do Differently Next Time

Start with a read-only inventory of both systems and save sanitized evidence before any write path is built.

Make dry-run planning the stable interface between durable data and writes. Every candidate should have a reason-coded action before live mode exists.

Treat holds as first-class results. Missing dates, unsupported destination years, ambiguous matches, amount mismatches, and uncertain relation mappings should pause safely instead of being guessed.

Keep external writes and durable ledger writes separate at scale. Use re-read verification as the boundary between them.

Design process locks before scheduling unattended bulk runs. Locks should protect the board and operation, not individual item status fields.

## Warnings for Future AI Agents

Do not rework ingestion or parsing when the user asks for Supabase-to-Monday sync unless you find a real incompatibility with the sync contract.

Do not add new Monday helper columns for every workflow. Prefer a durable ledger, a reusable status field when the business needs it, or an external control table.

Do not trust GraphQL mutation success as final proof. The proof is the re-read state plus the durable ledger verification.

Do not include PHI, claim numbers, board IDs, credentials, exact operational counts, or live customer-specific evidence in a general KB entry.

Do not run broad writes while another bot or manual maintenance operation is active. Use a process lock or pause.
