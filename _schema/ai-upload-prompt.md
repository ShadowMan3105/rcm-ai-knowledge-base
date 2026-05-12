# KB Upload Prompt — Universal AI Instruction

## Purpose
Paste the block below into any AI system prompt or Project Instructions.
It triggers a standardized knowledge base upload offer at the end of any successful process, compliant with the v2 multi-agent protocol.

---

```
KNOWLEDGE BASE UPLOAD PROTOCOL (v2 — multi-agent safe)

This KB lives at https://github.com/ShadowMan3105/rcm-ai-knowledge-base
Before writing, you MUST read AI_PROTOCOL.md at the repo root.

When a process is complete and the user has confirmed the result works or is accepted,
present the following offer exactly once:

---
✅ Process complete.

Would you like to save this to the Knowledge Base?

Domain: [automations / research / rcm-operations / billing-config / executive-reports / consulting]
Kind:   [blueprint / lesson / sop / analysis / playbook / reference]
Entry title: [short descriptive title]
Tags:   [4-6 lowercase-kebab keywords]

Reply YES · NO · EDIT
---

On YES:
1. Run: python _tools/next_id.py <kebab-slug>   → get a stable id like KB-2026-NNNN-...
2. Create folder <domain>/<slug>/ with:
   - meta.json (validated against _schema/entry.schema.json)
   - report.md
   - lessons.md
   - revisions/<YYYY-MM-DD>-<your-canonical-agent-id>-initial.md
3. Set:
   - status:     "proposed" (unless the curator authorizes "active")
   - confidence: "low" | "medium" | "high"  (your honest self-assessment)
   - created_by: your canonical agent id (claude-opus-4-7, gpt-5, codex, …)
   - human_approved_by: the user's name only if they explicitly say "approve"
4. Run: python _tools/validate.py             (must pass)
5. Run: python _tools/rebuild_index.py         (regenerates index.json)
6. Commit: add(KB-2026-NNNN-slug): <short description>
7. Push.

On EDIT → show all files inline for the user to review before saving.
On NO  → close without saving.

---

CHALLENGING AN EXISTING ENTRY

If you discover an existing active entry is wrong or obsolete:
- DO NOT edit its report.md or lessons.md.
- Copy _schema/challenge-template.md → challenges/CH-YYYY-MM-DD-slug.md.
- Append your challenge id to the target's challenged_by; set its status to "challenged".
- Validate + rebuild_index + commit: challenge(KB-…): <one-line reason>.

---

CONTENT QUALITY RULES — apply to every entry without exception:

INCLUDE:
- The strategy or decision logic: why this approach over alternatives
- The reusable blueprint: steps, structure, or framework that works generically
- Confirmed mistakes: what failed, root cause, the rule extracted
- Warnings for future AI agents: specific traps this domain is prone to

EXCLUDE — these make the KB useless or unsafe:
- No specific names (patient/provider/clinic/staff)
- No specific identifiers (NPI, EIN, payer ID, board ID, account ID)
- No credentials (PATs, API keys, passwords, tokens)
- No specific dollar amounts, rates, or contract terms
- No raw operational data (claim numbers, live denial counts, date ranges from live systems)
- No session noise (intermediate errors immediately fixed, clarification back-and-forth)

TEST BEFORE SAVING: "Could a different organization in a different context use this
entry to solve the same class of problem?" If yes, save it. If no, generalize it.

STRUCTURE RULES:
- report.md: strategy first, blueprint second, reusable components third
- lessons.md: every mistake ends with one concrete rule ("never X" / "always verify Y")
- meta.json: tags reflect the problem domain, not the specific project name
- Minimum one mistake in lessons.md; if none occurred, note what assumptions were validated
- IDs and folder-slug must match (folder name == slug part of id)

Never upload without explicit user approval.
If uncertain about domain, kind, or tags, ask — do not guess.
```

---

## Version
v3.0 — 2026-05-11 (aligned with AI_PROTOCOL.md v1.0)
