# Lessons Learned — [Project Title]

> **Editing rules (v1.2):**
> 1. Existing `### Mistake N` blocks are **immutable** — never delete or rewrite a Mistake once committed. The point of this KB is that AIs lose memory; the mistake must stay on the record forever.
> 2. If you learn new info about an existing Mistake (e.g., the library bug was later fixed, the API now returns proper errors), append to that Mistake's `Subsequent Updates` block. **Outdated factual details inside the update** may be replaced; the Mistake heading and the original five fields stay.
> 3. New mistakes get a new `### Mistake N+1` block at the end.
> 4. Every Mistake must declare `Category` and `Severity` so AIs can filter relevance fast.

---

## Mistakes Made

### Mistake 1: [Short label]
- **Category:** `data-quality` | `api-integration` | `library-compat` | `parser` | `schema` | `process` | `strategy` | `security` | `performance` | `configuration` | `deployment`
- **Severity:** `low` | `medium` | `high`
- **What happened:** 
- **Root cause:** 
- **How it was caught:** 
- **Fix applied:** 
- **Rule extracted:** Never do X when Y. Always verify Z before proceeding.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*
  <!--
  - 2026-MM-DD by <agent-id>: <what changed in the world; the original Mistake stands>
  -->

### Mistake 2: [Short label]
- **Category:** 
- **Severity:** 
- **What happened:** 
- **Root cause:** 
- **How it was caught:** 
- **Fix applied:** 
- **Rule extracted:** 
- **Subsequent Updates:**

<!-- Add as many as needed. Never renumber existing mistakes. -->

---

## Categories cheat-sheet

| Category | Use when the error was about… |
|---|---|
| `data-quality` | Bad inputs, dirty data, false positives in extraction, miscounting |
| `api-integration` | Third-party API silent failures, missing fields, rate limits, auth |
| `library-compat` | Library version incompatibilities, missing exports, deprecated APIs |
| `parser` | Regex or text/PDF parser that misread structure |
| `schema` | Database schema, column type, missing FK, wrong primary key |
| `process` | Workflow/SOP step skipped or done out of order |
| `strategy` | Architectural decision later found wrong (e.g., placed component in wrong phase) |
| `security` | PHI leak risk, credential handling, permissions too broad |
| `performance` | Slow query, memory blow-up, unnecessary recomputation |
| `configuration` | Misconfigured tool (Monday.com columns, n8n credentials, eCW setup) |
| `deployment` | CI/CD, env vars, packaging, runtime environment mismatch |

Severity guide:
- `low` — annoyance, cosmetic, reworkable in < 30 min
- `medium` — wasted hours, required rework but no data loss / no client impact
- `high` — data corruption, client-visible error, financial discrepancy, security risk

---

## Assumptions That Were Wrong
<!-- List any assumptions made at the start that turned out to be incorrect. -->

## What to Do Differently Next Time
<!-- Concrete action items. Not vague advice. -->

## Warnings for Future AI Agents
<!-- Specific traps or pitfalls an AI would likely fall into on this topic. -->
