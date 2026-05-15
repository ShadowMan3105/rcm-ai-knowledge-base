# Lessons Learned - Paid Date Accounting Reconciliation With PDF Last-Resort Evidence

## Mistakes Made

### Mistake 1: Zeroing a mismatched accounting row before checking last-resort PDF evidence
- **Category:** `process`
- **Severity:** `high`
- **What happened:** A row that was missing from the current structured aggregate was treated as unsupported and set to zero/mismatched before payment PDFs were used as the final evidence layer.
- **Root cause:** The investigation path collapsed "missing from current paid-board aggregate" into "no payment," instead of treating it as an unresolved traceability gap.
- **How it was caught:** The user pointed out that many checks exist in payment PDFs and asked whether the incorrect rows had been cross-referenced against those PDFs.
- **Fix applied:** The affected rows were cross-checked against PDF extracts. Where the PDFs showed payment evidence, the visible accounting amounts were restored to PDF-backed totals while the accounting status remained mismatched because structured sources still disagreed.
- **Rule extracted:** Never zero, delete, or hide a paid-date accounting row solely because it is missing from the current structured aggregate. Always use PDFs as the last-resort evidence layer before deciding that no payment exists.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 2: Treating PDF-backed evidence as fully reconciled when structured sources still disagree
- **Category:** `data-quality`
- **Severity:** `high`
- **What happened:** A PDF cross-check could have been interpreted as enough to mark a row verified, even though the paid boards, database, or cache still did not explain the same total.
- **Root cause:** Amount correctness and structured-source reconciliation were not separated sharply enough.
- **How it was caught:** The correction required keeping the accounting issue searchable for future review while still showing the PDF-backed amount.
- **Fix applied:** The status policy was updated: if PDFs prove payment but structured systems still disagree, preserve the amount and keep the row in a mismatched accounting status.
- **Rule extracted:** Never mark a PDF-backed paid-date row fully verified until the structured sources also reconcile. Keep the mismatch status visible while preserving the payment amount.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 3: Reading the post-correction cache as if it were the original state
- **Category:** `process`
- **Severity:** `medium`
- **What happened:** During follow-up audit, the first comparison read a cache snapshot that already reflected the zeroed state, making the original amounts appear to be zero.
- **Root cause:** The audit did not initially distinguish pre-write evidence from post-write verification cache.
- **How it was caught:** The comparison output showed impossible "original" values and had to be corrected by reading the earlier run payload that contained the real previous row state.
- **Fix applied:** The cross-check script was changed to read both the final cache and the earlier pre-change cache/payload, separating current values from original values.
- **Rule extracted:** Never use a post-write cache row as proof of the original value. Preserve and read pre-write snapshots when auditing whether a correction was valid.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

## Assumptions That Were Wrong

The wrong assumption was that a row absent from current paid-board totals could safely be treated as extra or unsupported. In paid-date reconciliation, absence from a structured aggregate can also mean stale cache, failed sync, alias mismatch, date-basis mismatch, or a payment that is still only visible in source PDFs.

Another wrong assumption was that one accounting status can mean both "amount proven" and "all systems reconciled." These are different facts and should be represented separately: the amount can be visible from PDF evidence while the status stays mismatched until the durable structured sources catch up.

## What To Do Differently Next Time

Start with structured systems, but keep a defined escalation step to PDFs. Do not use PDFs first, because that makes the process slow and can bypass durable source-of-truth checks. Do not skip PDFs either, because they can prove real payment evidence when the structured layers have drifted.

Keep every correction auditable with pre-write values, desired values, source priority, PDF verdict when used, and a post-write re-read.

Treat a mismatched status as an operational search signal, not as a reason to hide the amount. Dashboards can remain useful while showing that the row still needs source-system reconciliation.

## Warnings for Future AI Agents

Do not store live board IDs, item IDs, claim numbers, patient names, exact payment totals, or raw PDF line data in the general KB. Keep those in local audited evidence files or controlled internal systems.

Do not allow a later sync to zero a PDF-backed payment row without rerunning the full source-priority path.

Do not use payment PDFs as the routine first pass. They are expensive and should be used after Monday, paid boards, Supabase, and n8n cannot explain the mismatch.

Do not mark a PDF-backed row as verified just because the PDF amount exists. Verification requires structured-source reconciliation too.
