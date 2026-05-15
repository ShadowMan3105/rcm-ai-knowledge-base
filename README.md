# RCM AI Knowledge Base

A multi-agent-safe repository of strategies, blueprints, lessons learned, and analyses from RCM, billing operations, automation, and consulting projects.

**Purpose:** Give any AI agent or human collaborator a verified head start — no hallucinations, no reinventing the wheel, no last-AI-overwrites-previous-AI breakage.

**What lives here:** Final project reports, decision rationales, confirmed mistakes and their root causes, reusable templates, multi-agent revisions and challenges.

**What does NOT live here:** Patient data, PHI, HIPAA-regulated content, credentials, API keys, payer-specific rates, or live operational data.

---

## ⚠️ For AI agents — start here

- **Mandatory operating directive?** → read [`AGENTS.md`](AGENTS.md) first, then follow `AI_PROTOCOL.md` and `READ_PROTOCOL.md`.
- **Reading the KB?** → see [`READ_PROTOCOL.md`](READ_PROTOCOL.md) and the copy-paste prompt in [`_schema/ai-read-prompt.md`](_schema/ai-read-prompt.md).
- **Using Graphify?** → read [`_graph/README.md`](_graph/README.md) and use `_graph/` only as advisory navigation after `index.json`.
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
7. Optionally read `_graph/GRAPH_REPORT.md` and `_graph/incremental-latest/GRAPH_REPORT.md` for navigation hints, then verify against source files.

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
├── compose.local-ai.yml    ← Ollama + Graphify runner; standalone n8n only by profile
├── compose.existing-n8n.yml ← Attach Ollama to an existing n8n Docker network
├── _graph/                 ← Published advisory Graphify snapshots
│   ├── GRAPH_REPORT.md     ← Full advisory graph report when generated
│   ├── graph.json          ← Full advisory graph data
│   └── incremental-latest/ ← Recent-change graph from the production runner
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
│   ├── next_id.py          ← Get next stable KB ID
│   └── update_graph_snapshot.py ← Local Graphify publish helper
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

This KB can be navigated with Graphify as an advisory knowledge graph layer.
The approved pattern is local generation plus cloud-readable publication:

```text
local Docker/Ollama -> Graphify -> _graph/ snapshot -> GitHub -> cloud AI reads _graph/
```

The graph does not replace `AI_PROTOCOL.md`, `AGENTS.md`, `index.json`,
`meta.json`, `report.md`, `lessons.md`, `challenges/`, or `patches/`.

Local Ollama workflow:

```bash
python _tools/update_graph_snapshot.py --backend ollama --model-label ollama:qwen2.5-coder:7b --commit --push
```

Docker workflow:

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml up -d ollama
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml exec ollama ollama pull qwen2.5-coder:7b
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml --profile graphify run --rm -e OLLAMA_MODEL=qwen2.5-coder:7b graphify-runner python _tools/update_graph_snapshot.py --backend ollama --model-label ollama:qwen2.5-coder:7b --changed-since "8 hours ago"
```

Use `--profile standalone-n8n` only if there is no existing n8n container.

Current production cadence:

```text
02:00, 10:00, and 18:00 local time
model: ollama:qwen2.5-coder:7b
scope: changed files from the previous 8 hours
published output: _graph/incremental-latest/
```

Cloud AI read flow:

1. Read `AGENTS.md`, `READ_PROTOCOL.md`, `AI_PROTOCOL.md`, and `index.json`.
2. Read `_graph/GRAPH_REPORT.md` if present.
3. Read `_graph/incremental-latest/GRAPH_REPORT.md` when the question involves recent repo changes.
4. Use `_graph/graph.json` and `_graph/incremental-latest/graph.json` only for navigation.
5. Verify conclusions against source KB files before acting.

See `GRAPHIFY_INTEGRATION.md` for safety rules, commit policy, and query examples.
See `docs/local-graphify-n8n.md` for the local Docker/n8n operating model.
<!-- GRAPHIFY-KB-LAYER:END -->
