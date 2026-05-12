# RCM AI Knowledge Base

A multi-agent-safe repository of strategies, blueprints, lessons learned, and analyses from RCM, billing operations, automation, and consulting projects.

**Purpose:** Give any AI agent or human collaborator a verified head start — no hallucinations, no reinventing the wheel, no last-AI-overwrites-previous-AI breakage.

**What lives here:** Final project reports, decision rationales, confirmed mistakes and their root causes, reusable templates, multi-agent revisions and challenges.

**What does NOT live here:** Patient data, PHI, HIPAA-regulated content, credentials, API keys, payer-specific rates, or live operational data.

---

## ⚠️ Before you write anything

**Read [`AI_PROTOCOL.md`](AI_PROTOCOL.md) first.** It is the contract every agent (Claude, GPT, Codex, Gemini, Ollama, etc.) must follow. Key points:

- Every entry has an immutable `id` (`KB-YYYY-NNNN-slug`).
- Active entries are read-only for content. To dispute one, open a **challenge** in `/challenges/`.
- After any change, run `python _tools/validate.py` and `python _tools/rebuild_index.py`. Never hand-edit `index.json`.
- Some fields (`id`, `created_at`, `created_by`, `supersedes`) are immutable.

---

## How to use this KB (for AI agents)

1. Fetch [`index.json`](index.json) — full machine-readable map of entries, stats, and open challenges.
2. Filter by `tags`, `domain`, `kind`, or `status`.
3. Trust order: `active` > `proposed` > `challenged` >> `deprecated` / `superseded`.
4. Read `report.md` for the strategy/blueprint and `lessons.md` for pitfalls.
5. Check `meta.json` for `last_verified`, `confidence`, and `challenged_by`.
6. Before applying an `active` entry, check if `superseded_by` is set.

## Lifecycle of an entry

```
proposed ──► active ──► challenged ──► (deprecated | superseded)
                  └─────────────────► deprecated  (curator-decided)
```

## How to challenge an entry

If you (an AI) believe an `active` entry is wrong or obsolete:

1. **Do not edit** its `report.md` or `lessons.md`.
2. Copy `_schema/challenge-template.md` to `challenges/CH-YYYY-MM-DD-slug.md`.
3. Append your challenge ID to the target's `challenged_by` and set its `status` to `challenged`.
4. Validate, rebuild index, commit.
5. Dr. Seidel resolves.

Full rules: [`AI_PROTOCOL.md`](AI_PROTOCOL.md) §4 and §7.

---

## Repository layout

```
.
├── AI_PROTOCOL.md          ← Multi-agent contract — READ FIRST
├── README.md
├── SETUP.md
├── index.json              ← Auto-generated. Do not hand-edit.
├── _schema/                ← JSON schemas + templates
│   ├── entry.schema.json
│   ├── challenge.schema.json
│   ├── revision.schema.json
│   ├── meta-template.json
│   ├── challenge-template.md
│   ├── report-template.md
│   └── lessons-template.md
├── _tools/
│   ├── rebuild_index.py    ← Run after any change
│   ├── validate.py         ← Run before commit
│   └── next_id.py          ← Get next stable KB ID
├── challenges/             ← Open / resolved challenges
└── <domain>/<slug>/
    ├── meta.json
    ├── report.md
    ├── lessons.md
    └── revisions/          ← Immutable history snapshots
```

## Domain folders

| Folder | What it contains |
|---|---|
| `automations/` | n8n workflows, Monday.com automations, AI agents, API integrations |
| `research/` | Payer analysis, timely filing, taxonomy, NPI, regulatory research |
| `rcm-operations/` | SOPs, onboarding frameworks, biller standards, denial management |
| `billing-config/` | eCW v12 setup, 837P/clearinghouse config, ERA/EFT enrollment |
| `executive-reports/` | Strategic summaries for ownership and management |
| `consulting/` | Advisory engagements, gap analyses, roadmaps |

---

## How to contribute

1. Complete a project or research task.
2. Read `AI_PROTOCOL.md` if you have not.
3. Get a stable ID: `python _tools/next_id.py my-slug` → `KB-2026-XXXX-my-slug`.
4. Create `<domain>/<id-slug>/` with `meta.json`, `report.md`, `lessons.md`, and `revisions/<date>-<agent>-initial.md`.
5. Run validators:
   ```bash
   python _tools/validate.py
   python _tools/rebuild_index.py
   ```
6. Commit with the conventional message: `add(KB-2026-XXXX): <short description>`.
7. Submit PR or push (contributors with write access).

---

## Maintainer
Dr. Seidel — RCM Operations & AI Strategy

## Protocol version
v1.0 (2026-05-11) — see `AI_PROTOCOL.md`.
