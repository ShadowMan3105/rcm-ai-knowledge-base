# Lessons Learned - Universal Claims Ingestion With Transient Cache And Durable Dedupe

## Mistakes Made

### Mistake 1: Treating row-level dedupe as possible before parsing
- **What happened:** The design initially discussed early dedupe in a way that could be interpreted as skipping file rows before normalized rows existed.
- **Root cause:** File-level dedupe and row-level dedupe were not separated clearly enough.
- **How it was caught:** The operational requirement showed that multiple input paths can produce the same claim data, but row identity is not knowable until the report is parsed and normalized.
- **Fix applied:** The design now allows only file/source-level checks before parsing and performs row-level dedupe after deterministic normalization.
- **Rule extracted:** Never claim row-level dedupe before parsing; always separate file/source dedupe from row-level dedupe before designing an ingestion gate.

### Mistake 2: Treating n8n Data Tables like durable audit storage
- **What happened:** A historical backfill into n8n Data Tables reached the practical storage limit before the audit layer was complete.
- **Root cause:** The local automation cache was asked to behave like a warehouse instead of a bounded operations buffer.
- **How it was caught:** The backfill failed at the platform table-size boundary.
- **Fix applied:** The design was changed so n8n stores only transient staged rows while durable audit and dedupe evidence live in Supabase/Postgres.
- **Rule extracted:** Never use n8n Data Tables as the durable claims audit warehouse; always keep n8n staging bounded and move durable history into a database.

### Mistake 3: Uploading operational rows before registering audit context
- **What happened:** The first upload workflow draft focused on parsed, crosswalk, and final rows but did not register source-file and parse-batch audit rows first.
- **Root cause:** The upload path was built around row movement before run-level provenance was made mandatory.
- **How it was caught:** A pre-upload review showed that durable rows would be harder to trace back to a controlled source run.
- **Fix applied:** Source-file registration and parse-batch registration were added before row uploads, and row mappers were changed to carry the upload batch id.
- **Rule extracted:** Always register source-file and parse-batch audit context before uploading parsed or final claim rows.

### Mistake 4: Assuming workflow completion status is enough proof
- **What happened:** A controlled upload produced durable rows, but the workflow execution status still needed separate review.
- **Root cause:** Workflow execution state and database write verification were treated as the same kind of evidence.
- **How it was caught:** Database counts and totals showed the durable upload was present, while the orchestration layer still reported an unresolved execution state.
- **Fix applied:** The cache clear step was held, and the durable upload evidence was documented separately from workflow-execution status.
- **Rule extracted:** Never clear transient cache based only on partial evidence; always verify both durable storage state and workflow completion state before clearing staged rows.

## Assumptions That Were Wrong

The main wrong assumption was that the local automation cache could safely hold broad historical audit data. In practice, the cache should be small, bounded, and disposable after durable upload. The second wrong assumption was that a successful durable write automatically means the workflow execution lifecycle is clean; these must be checked separately.

## What to Do Differently Next Time

Design the audit schema before enabling row writes. Build source-file, parse-batch, row-audit, crosswalk, and final-row tables as a single storage contract.

Run the first real-file test only to a temporary or transient cache. Verify controls and dedupe before any durable write.

Keep the first durable upload separate from cache clearing. Upload, verify database state and totals, inspect workflow execution status, then clear in a separate controlled step.

Keep paid, denied, and pending report logic separate at the final-table level, but reuse the same feeder, audit, dedupe, and control-total gates.

## Warnings for Future AI Agents

Do not skip deterministic parsing because a file name looks familiar. File names are weak evidence unless combined with a stable hash or durable source registry.

Do not use paid AI APIs as an assumed dependency. The reusable pattern must work with n8n-native nodes, local/free extraction tools, and configured external tools.

Do not aggregate away CPT/service-line detail. The final operational row can be claim-level or date-of-service-level, but the audit layer must preserve service-line evidence.

Do not write to work-management boards before durable storage succeeds. Boards should be synchronized from durable final rows, not treated as the primary audit source.

Do not clear transient staging until durable rows, control totals, duplicate checks, and workflow execution state have all been verified.
