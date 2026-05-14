# Graphify Integration for RCM AI Knowledge Base

Status: proposed integration layer
Owner: Dr. Seidel / RCM Operations & AI Strategy
Scope: navigation, relationship discovery, and advisory knowledge-graph queries

---

## 1. Purpose

This repository remains the source of truth for RCM strategies, blueprints, lessons learned, challenges, patches, and curator-reviewed decisions.

Graphify adds a **knowledge graph layer** on top of the repository. Its purpose is to help humans and AI agents find relationships across entries faster:

- which strategies, lessons, challenges, patches, and domains are connected;
- which entries may duplicate, contradict, or supersede each other;
- which mistakes appear across multiple RCM areas;
- which automation, billing configuration, consulting, research, and operations documents should be read together;
- which open challenges or patches may affect a planned action.

Graphify is **advisory only**. It does not change the KB lifecycle or authority model.

---

## 2. Authority model

The authoritative order remains:

1. `AI_PROTOCOL.md`
2. `index.json`, rebuilt by `_tools/rebuild_index.py`
3. each entry's `meta.json`
4. `report.md`
5. `lessons.md`
6. `challenges/` and `patches/`
7. Graphify outputs (`graphify-out/`) as advisory navigation aids only

Graph-derived conclusions must never be treated as verified KB truth until converted into one of the existing governed paths:

- a new KB entry;
- a challenge in `challenges/`;
- a patch in `patches/`;
- a curator-approved supersession or deprecation.

---

## 3. Recommended architecture

```text
RCM AI Knowledge Base
├── protocol + schemas + validators      # authoritative rules
├── domain entries                       # authoritative content
├── challenges / patches                 # governed correction layer
├── .graphifyignore                      # graph input boundary
├── _tools/build_graphify_corpus.py      # curated graph corpus builder
├── _tools/run_graphify_kb.py            # repeatable graphify runner
└── graphify-out/                        # generated graph/report outputs
```

The integration uses a generated local corpus folder:

```text
.graphify-kb-corpus/
```

This folder is rebuilt from the KB and is not committed. It combines metadata and Markdown content into Graphify-friendly files so `meta.json`, `index.json`, `report.md`, and `lessons.md` can be read as one navigable knowledge surface.

Every AI agent must read `AGENTS.md` before using the graph. That file defines the mandatory operating contract: truth policy, authority order, verification gates, Graphify advisory boundaries, and controlled-tool rules.

---

## 4. Installation

Recommended install:

```bash
uv tool install graphifyy
```

Alternative installs:

```bash
pipx install graphifyy
pip install graphifyy
```

Optional extras for this repository:

```bash
pip install "graphifyy[openai]"   # OpenAI / OpenAI-compatible backend
pip install "graphifyy[gemini]"   # Gemini backend
pip install "graphifyy[ollama]"   # local Ollama backend
pip install "graphifyy[mcp]"      # expose graph as MCP tools
```

Register with an assistant if desired:

```bash
graphify install
```

---

## 5. Standard workflow

From the repository root:

```bash
python _tools/validate.py
python _tools/rebuild_index.py
python _tools/build_graphify_corpus.py
python _tools/run_graphify_kb.py --workflow extract --backend openai
```

This uses the headless Graphify command:

```bash
graphify extract .graphify-kb-corpus --backend openai
```

For assistant-style project mapping with flags such as `--no-viz` or `--wiki`:

```bash
python _tools/run_graphify_kb.py --workflow map --no-viz --wiki
```

This uses:

```bash
graphify .graphify-kb-corpus --no-viz --wiki
```

For a local-only backend:

```bash
OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=llama3.1 \
  python _tools/run_graphify_kb.py --workflow extract --backend ollama
```

For an IDE/assistant skill workflow:

```bash
python _tools/build_graphify_corpus.py
/graphify .graphify-kb-corpus --update
```

Query examples:

```bash
graphify query "what connects denial management to eCW configuration?"
graphify query "which challenged entries affect automation decisions?"
graphify path "timely filing" "claim scrubber"
graphify explain "KB lifecycle"
```

---

## 6. Commit policy

Do not commit generated Graphify output by default:

```text
.graphify-kb-corpus/
graphify-out/
.graphify/
.graphify_cache/
.graphify_labels.json
```

The graph can be regenerated from authoritative KB files. If the curator later wants a shareable graph artifact committed, update this policy and `.gitignore` explicitly in that PR.

---

## 7. Safety rules

Graphify must not ingest or generate:

- PHI;
- patient-level data;
- credentials;
- API keys;
- payer-specific rates;
- live operational exports;
- screenshots containing patient identifiers;
- unreviewed external files unless they are clearly safe for this KB.

Before running Graphify on new content, ensure the content is allowed by the repository's existing exclusion policy.

Do not use `graphify add <url>` for live client, payer, EHR, clearinghouse, or production data.

---

## 8. How to turn graph findings into KB changes

Use this decision table:

| Graph finding | KB action |
|---|---|
| Relationship between entries is useful but not corrective | mention it in a new report or future entry |
| Entry appears wrong, outdated, or contradicted | file a challenge |
| Typo, dead link, tag correction, library/version note | file a patch |
| New durable strategy or reusable workflow | create a new KB entry |
| Old strategy should no longer be used | curator decides deprecation or supersession |

Never edit immutable `### Mistake N` blocks directly. New information belongs in the permitted subsequent-update path or in a challenge/supersession flow.

---

## 9. Troubleshooting

### `graphify: command not found`

Use `uv tool install graphifyy` or `pipx install graphifyy`, then reopen the terminal.

### Headless extraction asks for an API key

When using `graphify extract`, choose a backend and provide the correct environment variable, for example:

```bash
python _tools/run_graphify_kb.py --backend openai
python _tools/run_graphify_kb.py --backend gemini
```

Set backend credentials only in your local shell environment. Never commit API keys or paste them into KB files.

### Graph output contains stale relationships

Run:

```bash
python _tools/rebuild_index.py
python _tools/build_graphify_corpus.py --clean
graphify extract .graphify-kb-corpus --force
```

### Graph output conflicts in Git

Regenerate from the current branch after resolving source-file conflicts. Treat `graphify-out/` as derived output, not as primary KB content.

---

## 10. Initial validation checklist

Before merging this integration:

- [ ] `python _tools/check_graphify_policy.py` passes.
- [ ] `python _tools/validate.py` passes or only emits accepted warnings.
- [ ] `python _tools/rebuild_index.py` runs cleanly.
- [ ] `python _tools/build_graphify_corpus.py` generates `.graphify-kb-corpus/`.
- [ ] `graphify --version` works locally.
- [ ] `python _tools/run_graphify_kb.py --dry-run` prints the expected command.
- [ ] `python _tools/run_graphify_kb.py --workflow map --no-viz --wiki --dry-run` prints the expected map command.
- [ ] No secrets or PHI are committed.
