# Lessons

## MarkItDown Is A Fallback, Not The Ledger Parser

MarkItDown is useful for converting many file types into Markdown for AI review, but that conversion is not the same as claims parsing.

In the controlled proof, MarkItDown preserved enough text to identify a denied-claims report, but not enough operational structure for the current Clinic HF parser to recover `dos_total` or `service_line` rows.

The prevention rule is simple: MarkItDown output must pass through the existing parser and control-total gates before any accounting or write decision.

## Strange Files Should Be Routed, Not Trusted

For unusual files, MarkItDown can help decide what the file is and which downstream path should handle it. It should not be treated as a completed extraction unless the downstream parser and validation checks prove the same row and amount structure expected from primary sources.

## Keep Accounting Gates Separate From Text Extraction

Text extraction can improve, change, or be swapped later. Accounting safety depends on separate gates:

- claim/DOS identity;
- service-line preservation;
- `dos_total` aggregation;
- source control totals;
- durable dedupe;
- transient staging verification;
- Supabase/Monday write verification.

Do not merge these gates into the extractor layer.
