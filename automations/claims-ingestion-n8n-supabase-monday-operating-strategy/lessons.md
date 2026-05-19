# Lessons Learned - Claims Ingestion From n8n To Supabase And Monday

## Mistakes Made

### Mistake 1: Letting a parser write directly to Monday
- **Category:** `strategy`
- **Severity:** `high`
- **What happened:** Early automation designs could be interpreted as letting a parser result flow directly into a work board.
- **Root cause:** Parsing, durable authority, and operational sync were not separated sharply enough.
- **How it was caught:** Real paid, denied, pending, and payment-detail runs showed that extraction quality, duplicate keys, and durable final rows must be proven before Monday writes.
- **Fix applied:** The strategy now gates all Monday writes behind Supabase durable final rows, dry-run planning, controlled write batches, and Monday re-read verification.
- **Rule extracted:** Never write parser output directly to Monday. Always parse -> validate -> stage -> upload to durable storage -> dry-run -> write Monday -> re-read -> align ledger.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 2: Treating n8n Data Tables as the permanent claims warehouse
- **Category:** `strategy`
- **Severity:** `high`
- **What happened:** Some cache/staging patterns risked preserving large historical claim evidence inside n8n Data Tables.
- **Root cause:** A convenient workflow-local table was treated as if it had the same durability, query control, and audit value as Postgres.
- **How it was caught:** Ingestion and migration work showed that Data Tables are useful for bounded staging/caches, while durable audit and dedupe belong in Supabase/Postgres.
- **Fix applied:** n8n Data Tables are now bounded transient buffers or rebuildable caches. Supabase/Postgres stores durable source, audit, crosswalk, final, and ledger rows.
- **Rule extracted:** Never use n8n Data Tables as durable claims storage. Keep them small, bounded, and clearable after durable proof.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 3: Attempting row-level dedupe before deterministic parsing
- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** File names and source labels were sometimes tempting to use as evidence that rows already existed.
- **Root cause:** File/source dedupe and row-level claim dedupe were mixed together.
- **How it was caught:** Multi-source ingestion showed that the same claim can arrive from different reports and formats, while row identity is knowable only after normalization.
- **Fix applied:** Only exact file/source evidence is checked before parsing. Row-level dedupe happens after normalized persisted keys are produced.
- **Rule extracted:** Never claim row-level dedupe before parsing. Build durable row identity from normalized parsed fields.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 4: Aggregating away service-line evidence too early
- **Category:** `parser`
- **Severity:** `high`
- **What happened:** Operational outputs often need claim/date-of-service totals, which can make service-line details look unnecessary.
- **Root cause:** Operational reporting needs were confused with audit needs.
- **How it was caught:** Paid, denied, and spreadsheet workflows required CPT/service-line traceability to explain totals, modifiers, duplicate candidates, and parser failures.
- **Fix applied:** The parser now preserves service-line audit rows first and derives claim/date-of-service totals after that audit layer.
- **Rule extracted:** Never aggregate away service-line evidence before audit storage. Operational totals are derived outputs, not replacements for source detail.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 5: Clearing transient staging before all proof existed
- **Category:** `process`
- **Severity:** `high`
- **What happened:** A staged upload could appear complete from one evidence path while another path, such as workflow execution state or durable count verification, still needed review.
- **Root cause:** Workflow status, database state, and cache state were treated as one proof.
- **How it was caught:** Durable upload checks and execution-state checks did not always mature at the same time.
- **Fix applied:** Cache clearing became a separate gate after durable counts, totals, duplicate checks, and workflow execution proof.
- **Rule extracted:** Never clear transient staging until durable rows, control totals, duplicate checks, and workflow execution state have all been verified.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 6: Trusting Monday manual fields as canonical evidence
- **Category:** `process`
- **Severity:** `high`
- **What happened:** Manual board fields, especially on pending queues, could be mistaken for official claim-status evidence.
- **Root cause:** Operational staff workflow state and official report evidence were not kept separate.
- **How it was caught:** Pending reconciliation rules showed that manual fields can be useful for human work but cannot prove paid or denied status.
- **Fix applied:** Pending changes are driven only by official paid or denied evidence and durable final rows. Manual pending fields are left untouched by canonical sync.
- **Rule extracted:** Never use manual Monday fields as evidence to change canonical claim status. Use official source reports and Supabase durable rows.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 7: Assuming GraphQL freedom is faster than controlled tools
- **Category:** `api-integration`
- **Severity:** `high`
- **What happened:** Free-form production GraphQL can look faster for Monday mutations but creates high risk around column IDs, board schemas, relation shapes, and partial failures.
- **Root cause:** The write path optimized for immediate flexibility instead of repeatable safety.
- **How it was caught:** Monday writes failed when assumed column IDs or relation behavior did not match the live board.
- **Fix applied:** The strategy prefers controlled wrappers, current schema reads, allowlisted operations, dry-run ledgers, small proof writes, and re-read verification.
- **Rule extracted:** Prefer controlled tools over free-form production GraphQL. Never mutate Monday without dry-run, current schema proof, and post-write verification.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 8: Preserving too much raw execution payload
- **Category:** `security`
- **Severity:** `medium`
- **What happened:** Heavy parser workflows can push large upstream context and claim data into execution history if not controlled.
- **Root cause:** Execution logs were treated as harmless debugging output instead of a potential data-retention surface.
- **How it was caught:** Claim workflows involve sensitive operational data and can produce large payloads.
- **Fix applied:** Runners should return sanitized proof fields, reduce saved execution payloads for heavy parser jobs, and keep durable evidence in Supabase/Postgres instead of n8n execution history.
- **Rule extracted:** Do not preserve bulky or sensitive parser payloads in workflow history. Store durable audit in the database and return sanitized verification summaries.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

## Assumptions That Were Wrong

The largest wrong assumption was that the parser was the center of the system. The durable truth boundary is more important than the parser itself. A parser can be replaced or improved, but the intake contract, audit layers, control totals, persisted keys, and sync gates must remain stable.

Another wrong assumption was that a successful Monday write means the row is synced. It is synced only after Monday is re-read and the Supabase ledger is aligned to the verified item.

## What to Do Differently Next Time

Design the durable schema and verification gates before building a new adapter.

Make adapters small and replaceable. Make the intake contract, persisted keys, service-line audit, control-total gate, durable upload, dry-run planner, and sync ledger stable.

Use source controls as hard gates. If controls do not match, retry extraction before warning or holding. Do not push uncertain rows downstream because the workflow ran successfully.

Keep caches cheap and rebuildable. Keep audit and final state durable.

## Warnings for Future AI Agents

Do not include PHI, credentials, claim lists, raw board exports, or exact customer operational rows in general KB entries.

Do not collapse paid, denied, and pending logic into one accounting meaning. They share ingestion plumbing but have different operational semantics.

Do not overwrite manual Monday workflow fields during canonical sync.

Do not trust stale n8n caches for production writes. Use them for low-token research, then re-read the target system before writing.

Do not treat this entry as permission to write production data. The write gates in the report are mandatory.
