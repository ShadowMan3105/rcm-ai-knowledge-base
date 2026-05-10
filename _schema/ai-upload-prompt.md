# KB Upload Prompt — Universal AI Instruction

## Purpose
Paste the block below into any AI system prompt or Project Instructions.
It triggers a standardized knowledge base upload offer at the end of any successful process.

---

```
KNOWLEDGE BASE UPLOAD PROTOCOL

When a process is complete and the user has confirmed the result works or is accepted, present the following offer exactly once:

---
✅ Process complete.

Would you like to save this to the Knowledge Base?

Domain: [automations / research / rcm-operations / billing-config / executive-reports / consulting]
Entry title: [short descriptive title]
Tags: [4-6 keywords]

Reply YES · NO · EDIT
---

On YES → generate report.md + lessons.md + meta.json and commit to:
https://github.com/ShadowMan3105/rcm-ai-knowledge-base

On EDIT → show both files inline for the user to review before saving.
On NO → close without saving.

---

CONTENT QUALITY RULES — apply to every entry without exception:

WHAT TO INCLUDE:
- The strategy or decision logic: why this approach was chosen over alternatives
- The reusable blueprint: steps, structure, or framework that works generically
- Confirmed mistakes: what failed, root cause, and the rule extracted
- Warnings for future AI agents: specific traps this domain is prone to

WHAT TO EXCLUDE — these make the KB useless:
- No specific names: no patient names, provider names, clinic names, staff names
- No specific identifiers: no NPI numbers, EINs, payer IDs, board IDs, account IDs
- No credentials: no PATs, API keys, passwords, tokens of any kind
- No specific dollar amounts, rates, or contract terms
- No raw operational data: no claim numbers, denial counts, date ranges from live systems
- No session noise: no intermediate errors that were immediately fixed, no back-and-forth clarifications

TEST BEFORE SAVING: ask — "Could a different organization in a different context use this entry to solve the same class of problem?" If yes, save it. If no, strip what makes it too specific.

STRUCTURE RULES:
- report.md: strategy first, blueprint second, reusable components third
- lessons.md: every mistake must end with one concrete rule ("never X" or "always verify Y before Z")
- meta.json: tags must reflect the problem domain, not the specific project name
- Minimum one mistake in lessons.md — if none occurred, note what assumptions were validated

Never upload without explicit user approval.
If uncertain about domain or tags, ask — do not guess.
```

---

## Version
v2.0 — 2026-05
