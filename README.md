# RCM AI Knowledge Base

A multi-agent-safe repository of strategies, blueprints, lessons learned, and analyses from RCM, billing operations, automation, and consulting projects.

**Purpose:** Give any AI agent or human collaborator a verified head start — no hallucinations, no reinventing the wheel, no last-AI-overwrites-previous-AI breakage.

**What lives here:** Final project reports, decision rationales, confirmed mistakes and their root causes, reusable templates, multi-agent revisions and challenges.

**What does NOT live here:** Patient data, PHI, HIPAA-regulated content, credentials, API keys, payer-specific rates, or live operational data.

---

## ⚠️ For AI agents — start here

- **Mandatory operating directive?** → read [`AGENTS.md`](AGENTS.md) first, then follow `AI_PROTOCOL.md` and `READ_PROTOCOL.md`.
- **Reading the KB?** → see [`READ_PROTOCOL.md`](READ_PROTOCOL.md) and the copy-paste prompt in [`_schema/ai-read-prompt.md`](_schema/ai-read-prompt.md).
- **Writing to the KB?** → see [`AI_PROTOCOL.md`](AI_PROTOCOL.md) (this is the contract every agent must follow). Key points:

- Every entry has an immutable `id` (`KB-YYYY-NNNN-slug`).
- Active entries are read-only for content. To **dispute** a strategy/conclusion, open a **challenge** in `/challenges/`. To make a **surface correction** (typo, dead link, lesson subsequent update), file a **patch** in `/patches/`.
- `lessons.md` is append-only. `### Mistake N` blocks are immutable — once recorded, the mistake stays on the record forever, even if the underlying bug is later fixed. New info goes into the `Subsequent Updates` block.
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
                  └────────────────► deprecated  (curator-decided)
```

## Challenge vs Patch — which one do I file?

| | **Challenge** | **Patch** |
|---|---|---|
| When | You doubt the **strategy, conclusion, or correctness** of the entry | The fix is **superficial** — typo, dead link, wrong tag, library version in a code example, appending to a `Subsequent Updates` block |
| Folder | `challenges/CH-YYYY-MM-DD-slug.md` | `patches/PA-YYYY-MM-DD-slug.md` |
| Template | `_schema/challenge-template.md` | `_schema/patch-template.md` |
| Effect on target entry | Status becomes `challenged`; curator review required | Status unchanged; merges on CI green |
| Curator review | Required | Optional |
| Touches `### Mistake N` block | Never directly (resolved via supersede if accepted) | Never deletes/rewrites — only appends to `Subsequent Updates` |

If you start writing a patch and find yourself questioning the strategy, stop and convert it to a challenge.

Full rules: [`AI_PROTOCOL.md`](AI_PROTOCOL.md) §4 (paths A–D), §4.5 (lessons.md), §7 (challenge resolution), §13 (patches).

---

## Repository layout

```
.
├── AI_PROTOCOL.md          ← Multi-agent contract — READ FIRST
├── AGENTS.md               ← Mandatory machine-friendly operating directive
├── README.md
├── SETUP.md
├── index.json              ← Auto-generated. Do not hand-edit.
├── _schema/                ← JSON schemas + templates
│   ├── entry.schema.json
│   ├── challenge.schema.json
│   ├── patch.schema.json
│   ├── revision.schema.json
│   ├── tags-canonical.json ← Allowed tags per domain (warn-only enforcement)
│   ├── meta-template.json
│   ├── challenge-template.md
│   ├── patch-template.md
│   ├── report-template.md
│   └── lessons-template.md
├── _tools/
│   ├── rebuild_index.py    ← Run after any change
│   ├── validate.py         ← Run before commit (emits WARN for staleness + non-canonical tags)
│   └── next_id.py          ← Get next stable KB ID
├── challenges/             ← Substantive disputes (curator-resolved)
├── patches/                ← Surface corrections (CI-green merge)
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
v1.2 (2026-05-12) — see `AI_PROTOCOL.md`.

<!-- GRAPHIFY-KB-LAYER:START -->
## Optional Graphify knowledge graph layer

This KB can be navigated with Graphify as an advisory knowledge graph layer. The graph helps agents and humans discover relationships across entries, lessons, challenges, patches, and domains, but it does not replace `AI_PROTOCOL.md`, `index.json`, `meta.json`, `report.md`, or `lessons.md`.

Standard workflow:

```bash
python _tools/validate.py
python _tools/rebuild_index.py
python _tools/build_graphify_corpus.py
python _tools/run_graphify_kb.py --workflow extract --backend openai
```

For assistant-style project mapping with visualization flags:

```bash
python _tools/run_graphify_kb.py --workflow map --no-viz --wiki
```

See `GRAPHIFY_INTEGRATION.md` for safety rules, commit policy, and query examples.
<!-- GRAPHIFY-KB-LAYER:END -->
