# MarkItDown As Secondary Extractor For Claims Ingestion

## Summary

MarkItDown is approved only as a secondary extractor or document-preview layer for unusual files in the Clinic HF claims ingestion process.

It converts many document types into Markdown that is easy for an AI agent to read. That is useful for file triage, previewing unfamiliar inputs, or attempting a fallback extraction when the normal text path fails.

It is not approved as the primary claims parser or as an accounting source of truth.

## Decision

Use MarkItDown as a fallback before the existing parser-normalizer:

`file intake -> extractor selection -> MarkItDown fallback or preview -> existing claims parser -> control totals -> dedupe -> transient staging -> Supabase/Monday writes`

The existing claims parser and n8n/Supabase gates remain authoritative for operational claims work.

## What MarkItDown Does

MarkItDown is a Python document-to-Markdown converter for LLM and text-analysis pipelines. It supports PDFs, Word, PowerPoint, Excel, HTML, CSV, JSON, XML, ZIP files, images, audio, YouTube URLs, and EPub, depending on optional dependencies.

For the inspected version, PDF support uses common extraction libraries such as `pdfminer.six` and `pdfplumber`. XLSX support uses `pandas` and `openpyxl`.

The useful part is not medical-billing intelligence. The useful part is one common conversion interface that can produce readable Markdown from many file types.

## What It Does Not Do

MarkItDown does not understand Clinic HF claim accounting. It does not natively create:

- `dos_total` rows;
- service-line audit rows in the project schema;
- claim-number plus DOS dedupe keys;
- paid, denied, and pending precedence;
- control-total validation;
- check/payment reconciliation;
- Supabase or Monday write plans.

For that reason it must not drive operational writes by itself.

## Verification Evidence

Repository inspected:

- Source: `microsoft/markitdown`
- Inspected HEAD: `a51f725d7ff4cdfe3bb6ad2ce2c04d98bf5f1f00`

Controlled proof:

- MarkItDown was installed in a temporary virtual environment with PDF support only.
- A real denied-claims PDF was converted.
- The output preserved enough text to identify the document and report markers.
- When that output was fed into the current Clinic HF parser, the parser produced only header rows:
  - `header=2`
  - `dos_total=0`
  - `service_line=0`

Existing parser verification:

- The current local parser test passed paid, denied, pending, and multi-service claim/DOS aggregation fixtures.
- This confirms the current parser still handles the operational accounting structure that MarkItDown did not recover in the proof sample.

## Approved Uses

Use MarkItDown for:

- previewing unfamiliar document formats;
- strange files that are not clearly paid, denied, or pending claims reports;
- DOCX, PPTX, HTML, ZIP, CSV, JSON, XML, and mixed-office files where a Markdown preview helps an agent route the file;
- a secondary text extraction attempt after the normal extractor fails;
- OCR or Document Intelligence experiments only behind explicit hold gates and PHI-safe handling.

## Prohibited Uses

Do not use MarkItDown alone for:

- final paid, denied, or pending ingestion;
- payment or check reconciliation;
- claim/DOS dedupe decisions;
- control-total pass/fail decisions;
- Monday item creates, updates, archives, or status changes;
- Supabase inserts, updates, or accounting alignment;
- replacing the existing n8n/Supabase validation chain.

## Required Adoption Gate

Before MarkItDown can be enabled in any production ingestion route, run a benchmark in shadow mode across representative files:

- paid claims PDF;
- denied claims PDF;
- pending claims PDF;
- all-claim report PDF;
- payment/EOB or check PDF;
- scanned/image-heavy PDF;
- DOCX/PPTX/XLSX or other unusual office file.

The benchmark must compare MarkItDown output against the existing extraction routes and require exact or better recovery of:

- report type;
- claim number;
- DOS;
- patient and practice identity where needed;
- CPT/service-line detail;
- billed, allowed, paid, and denial fields;
- file or provider control totals.

If those checks fail, MarkItDown may still remain useful as a preview/fallback, but the batch must stay in hold status and must not write to durable or operational systems.

## Operational Rule

Treat MarkItDown output as untrusted intermediate text. It can help an agent understand or route an unusual file, but all claims-accounting conclusions must still pass through the existing parser, control-total checks, dedupe logic, and write gates.
