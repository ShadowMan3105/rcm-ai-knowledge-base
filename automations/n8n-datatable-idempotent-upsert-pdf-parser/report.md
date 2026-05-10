# n8n DataTable Workflow Pattern with Idempotent Upsert + PDF Parser Architecture

## Strategy

**Goal**: build an n8n-based ingestion pipeline that converts vendor-exported PDF reports into a normalized, deduplicated, queryable dataset, while keeping the IA layer as a manual consultant (zero per-token cost during runtime).

**Core architectural decisions**:

1. **n8n as the orchestrator, not the developer's IDE.** Workflows are persisted via the SDK (validate_workflow → update_workflow → test_workflow loop). UI editing is reserved for irreversible inspections; everything reproducible goes through code.

2. **Native Data Tables over external DBs for the ingestion cache.** SQLite, `better-sqlite3`, `fs`, `crypto`, `process.env` are blocked inside n8n Code nodes for security reasons. Native Data Tables provide upsert/get/delete operations that map cleanly to the operations a parser needs without leaving the n8n boundary.

3. **Deterministic batch_id with no time component.** A polynomial hash of the sorted file signatures (`filename|filesize` for each input) produces a stable identifier. Same set of inputs ⇒ same batch_id ⇒ idempotent upserts. Trades retry-history visibility for operational cleanliness — explicit decision worth surfacing.

4. **Three-table schema for the ingestion stage**: `parsed_records_cache`, `parser_errors`, `parser_batch_summary`. Plus a fourth table `standard_output` that materializes the public contract for downstream consumers. Separating these tables means a contract change to the public schema does not require reprocessing source PDFs.

5. **Feeder workflow on schedule** to populate `standard_output` from `parsed_records_cache`. Filter is `validation_status IN ('PASSED','WARNING')` — failed records stay in the cache for triage but never leak to consumers.

## Reusable Blueprint

### Workflow shape — main parser

```
Manual/File Trigger
  └─ Extract Text From File (binary → text)
      └─ Parse + Validate (Code node, runOnceForAllItems)
          ├─ Records branch → Explode → Upsert into cache table
          ├─ Errors branch  → Explode → Insert into errors table
          └─ Summary branch → Build summary row → Insert into batch_summary → Notify channel
```

Three parallel branches off the parser are required because the parser produces three semantic outputs at once. Sequential chaining causes item multiplication (N items × M items = N*M executions).

### Workflow shape — feeder

```
Schedule Trigger
  ├─ Get rows where validation_status='PASSED'
  └─ Get rows where validation_status='WARNING'
       └─ Merge (append) → Normalize to public schema → Upsert into standard_output
```

Two parallel `get` operations because n8n DataTable filters do not support `OR` across distinct values cleanly when both must materialize. Merge with `mode: 'append'` concatenates the two streams.

### DataTable node configuration that actually works

Two pieces are mandatory and almost always missed:

**`matchType` field** (when the operation accepts filters): the only valid enum values are `'anyCondition'` and `'allConditions'`. Any other value is rejected at runtime with `"unexpected match type"`.

**`columns` field shape** (for insert/upsert operations using auto-mapping):
```
columns: {
  mappingMode: 'autoMapInputData',
  matchingColumns: [],
  schema: [],
  attemptToConvertTypes: false,
  convertFieldsToString: false
}
```
The shape must be complete. Aliases such as `dataMode: 'autoMapInputData'` are silently accepted by some validators but rejected at runtime. Always use the full shape.

### Idempotency verification protocol

Run the workflow twice with the same input. For the upsert table, every cached row should satisfy:
- Same primary key (`id`) on both runs
- Same `createdAt` on both runs
- Only `updatedAt` differs

If any row gets a new PK on the second run, the upsert is broken (likely `matchType` or `matchingColumns` misconfigured).

## Reusable Components

### PDF text extraction strategy

For PDFs with **flat text content** (paragraphs, simple lists), Markdown converters are fine.

For PDFs with **columnar/tabular data**, Markdown converters destroy the spatial layout because they linearize text in reading order. Use a coordinate-aware extractor that returns `(x, y, text)` per word. Then:
- Group words into rows by approximately equal `y` (tolerance ~3 units)
- Identify the row matching the column header labels
- For each subsequent value row, assign each value to the column whose header has the closest `x` coordinate (tolerance ~50 units depending on font width)

This is far more robust than regex over linearized text when the source layout is grid-like.

### Validation gate for parsed financial data

If the source document contains a totals row or summary section, parse it independently and use it as a **post-extraction validation gate**:

```
parser_total_billed     == document_summary.billed     (within $0.01)
parser_total_paid       == document_summary.paid       (within $0.01)
... etc
```

If the deltas exceed the tolerance, set `validation_status='FAILED'` for the entire batch. Never write to the standard output until all summary fields match.

### Code node hygiene

The Code node language is sandboxed JavaScript with these restrictions:
- No `require` of external modules
- No filesystem, `crypto` (Node's), `process.env`
- The validator rejects template-literal-based dynamic code construction
- Use plain string concatenation for any code embedded as a string parameter

Practical implication: any "import a library" instinct must be replaced with a hand-rolled implementation or by moving that work outside the Code node (HTTP Request to a sidecar service is the standard escape hatch).

### Sticky note shape gotcha

The SDK serializes sticky note configuration in a way where passing `content` as an object inside `parameters` produces nested-object output. The runtime ignores it but the validator complains. Pass content as a raw string. This is cosmetic but recurs every time a workflow is re-deployed via the SDK.
