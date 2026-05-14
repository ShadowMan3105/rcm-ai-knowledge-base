# Graphify Integration for RCM AI Knowledge Base

Status: local-generation and published-navigation layer
Owner: Dr. Seidel / RCM Operations & AI Strategy
Scope: local graph generation, published advisory graph snapshots, and relationship discovery

---

## 1. Purpose

This repository remains the source of truth for RCM strategies, blueprints,
lessons learned, challenges, patches, and curator-reviewed decisions.

Graphify adds a knowledge graph layer on top of the repository. Its purpose is
to help humans and AI agents find relationships across entries faster:

- which strategies, lessons, challenges, patches, and domains are connected;
- which entries may duplicate, contradict, or supersede each other;
- which mistakes appear across multiple RCM areas;
- which automation, billing configuration, consulting, research, and operations
  documents should be read together;
- which open challenges or patches may affect a planned action.

Graphify is advisory only. It does not change the KB lifecycle or authority
model. The approved operating model is:

```text
local Docker/Ollama -> Graphify -> controlled _graph/ snapshot -> GitHub -> cloud AI reads _graph/
```

Cloud AIs must not connect to local Ollama. They read `_graph/` from GitHub and
verify every conclusion against source KB files.

---

## 2. Authority Model

The authoritative order remains:

1. `AI_PROTOCOL.md`
2. `AGENTS.md`
3. `index.json`, rebuilt by `_tools/rebuild_index.py`
4. each entry's `meta.json`
5. `report.md`
6. `lessons.md`
7. `challenges/` and `patches/`
8. published Graphify snapshot (`_graph/`) as advisory navigation only
9. raw local Graphify outputs (`graphify-out/`) as temporary working files only

Graph-derived conclusions must never be treated as verified KB truth until
converted into one of the existing governed paths:

- a new KB entry;
- a challenge in `challenges/`;
- a patch in `patches/`;
- a curator-approved supersession or deprecation.

---

## 3. Recommended Architecture

```text
RCM AI Knowledge Base
|-- protocol + schemas + validators      # authoritative rules
|-- domain entries                       # authoritative content
|-- challenges / patches                 # governed correction layer
|-- .graphifyignore                      # graph input boundary
|-- compose.local-ai.yml                 # local Ollama/Graphify stack
|-- compose.existing-n8n.yml             # attach Ollama to an existing n8n network
|-- docker/graphify-runner.Dockerfile    # local Graphify runner image
|-- _tools/build_graphify_corpus.py      # curated graph corpus builder
|-- _tools/run_graphify_kb.py            # repeatable Graphify runner
|-- _tools/publish_graph_snapshot.py     # controlled _graph publisher
|-- _tools/update_graph_snapshot.py      # local generation + commit helper
|-- graphify-kb-corpus/                  # generated Graphify input corpus, ignored
|   `-- graphify-out/                    # raw local generated output, ignored
`-- _graph/                              # controlled committed navigation snapshot
```

The integration uses a generated local corpus folder:

```text
graphify-kb-corpus/
```

This folder is rebuilt from the KB and is not committed. It combines metadata
and Markdown content into Graphify-friendly files so `meta.json`, `index.json`,
`report.md`, and `lessons.md` can be read as one navigable knowledge surface.

Published cloud-readable graph files live in:

```text
_graph/
|-- README.md
|-- GRAPH_REPORT.md
|-- graph.json
`-- manifest.json
```

Every AI agent must read `AGENTS.md` before using the graph. That file defines
the mandatory operating contract: truth policy, authority order, verification
gates, Graphify advisory boundaries, and controlled-tool rules.

---

## 4. Local Docker Stack

Use this mode when you already have n8n running in Docker. This is the preferred
mode for the current environment.

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml up -d ollama
```

The override attaches Ollama to the existing n8n Docker network:

```text
n8n-docker_default
```

Then n8n can call Ollama at:

```text
http://ollama:11434
```

If the existing n8n network name differs, set:

```bash
N8N_DOCKER_NETWORK=<your-existing-n8n-network>
```

Use this standalone mode only when you do not already have n8n:

```bash
cp .env.example .env
docker compose -f compose.local-ai.yml --profile standalone-n8n up -d ollama postgres n8n
```

Pull a local model once:

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml exec ollama ollama pull llama3.1
```

Run Graphify locally through Docker:

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml --profile graphify run --rm graphify-runner
```

Publish and push the controlled `_graph/` snapshot from the host or runner:

```bash
python _tools/update_graph_snapshot.py --backend ollama --commit --push
```

For n8n, configure Ollama credentials with:

```text
http://ollama:11434
```

From the host machine, Ollama is available at:

```text
http://localhost:11434
```

---

## 5. Installation Without Docker

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
pip install "graphifyy[openai]"
pip install "graphifyy[gemini]"
pip install "graphifyy[ollama]"
pip install "graphifyy[mcp]"
```

Register with an assistant if desired:

```bash
graphify install
```

---

## 6. Standard Workflows

Build the curated corpus:

```bash
python _tools/validate.py
python _tools/rebuild_index.py
python _tools/build_graphify_corpus.py --strict-secrets
```

Headless cloud/API extraction:

```bash
python _tools/run_graphify_kb.py --workflow extract --backend openai
```

Local Ollama extraction:

```bash
OLLAMA_BASE_URL=http://localhost:11434/v1 OLLAMA_MODEL=llama3.1 \
  python _tools/run_graphify_kb.py --workflow extract --backend ollama --max-concurrency 1
```

When using Graphify's Ollama backend directly, `OLLAMA_BASE_URL` must point to
Ollama's OpenAI-compatible endpoint:

```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
```

Graphify's Ollama backend may require `OLLAMA_API_KEY` even for a local
server. Use a non-secret local placeholder:

```bash
OLLAMA_API_KEY=ollama-local
```

Assistant-style project mapping:

```bash
python _tools/run_graphify_kb.py --workflow map --no-viz --wiki
```

Publish a controlled `_graph/` snapshot:

```bash
python _tools/publish_graph_snapshot.py --backend ollama --model-label ollama:llama3.1
```

Full local update with optional Git commit/push:

```bash
python _tools/update_graph_snapshot.py --backend ollama --commit --push
```

---

## 7. Commit Policy

Do not commit raw generated Graphify output:

```text
graphify-kb-corpus/
.graphify-kb-corpus/
graphify-out/
.graphify/
.graphify_cache/
.graphify_labels.json
```

Commit only the controlled `_graph/` snapshot. `_graph/manifest.json` must record
the source commit, branch, backend, model label, Graphify version if available,
published files, graph counts if available, and verification status.

If `_graph/graph.json` or `_graph/GRAPH_REPORT.md` contains sensitive patterns,
publication must fail.

If the curator later wants additional graph artifacts committed, update this
policy explicitly in the same PR.

---

## 8. Safety Rules

Graphify must not ingest or generate:

- PHI;
- patient-level data;
- credentials;
- API keys;
- payer-specific rates;
- live operational exports;
- screenshots containing patient identifiers;
- unreviewed external files unless they are clearly safe for this KB.

Before running Graphify on new content, ensure the content is allowed by the
repository's existing exclusion policy.

Do not use `graphify add <url>` for live client, payer, EHR, clearinghouse, or
production data.

---

## 9. How To Turn Graph Findings Into KB Changes

| Graph finding | KB action |
|---|---|
| Relationship between entries is useful but not corrective | mention it in a new report or future entry |
| Entry appears wrong, outdated, or contradicted | file a challenge |
| Typo, dead link, tag correction, library/version note | file a patch |
| New durable strategy or reusable workflow | create a new KB entry |
| Old strategy should no longer be used | curator decides deprecation or supersession |

Never edit immutable `### Mistake N` blocks directly. New information belongs
in the permitted subsequent-update path or in a challenge/supersession flow.

---

## 10. Troubleshooting

### `graphify: command not found`

Use `uv tool install graphifyy` or `pipx install graphifyy`, or run the local
Docker `graphify-runner` service.

### Ollama is unavailable from n8n

Inside Docker, use:

```text
http://ollama:11434
```

Do not use `localhost` from inside the n8n container.

### Ollama is unavailable from the host

From the host, use:

```text
http://localhost:11434
```

Check the service:

```bash
docker compose -f compose.local-ai.yml ps ollama
```

### Graph output contains stale relationships

Run:

```bash
python _tools/rebuild_index.py
python _tools/build_graphify_corpus.py --clean --strict-secrets
python _tools/update_graph_snapshot.py --backend ollama --commit --push
```

### Graph output conflicts in Git

Regenerate from the current branch after resolving source-file conflicts. Treat
`graphify-kb-corpus/graphify-out/` as derived local output and `_graph/` as a published advisory
cache.

---

## 11. Validation Checklist

- [ ] `python _tools/check_graphify_policy.py` passes.
- [ ] `python _tools/validate.py` passes or only emits accepted warnings.
- [ ] `python _tools/rebuild_index.py` runs cleanly.
- [ ] `python _tools/build_graphify_corpus.py --strict-secrets` generates `graphify-kb-corpus/`.
- [ ] `python _tools/run_graphify_kb.py --dry-run` prints the expected extract command.
- [ ] `python _tools/run_graphify_kb.py --workflow map --no-viz --wiki --dry-run` prints the expected map command.
- [ ] `python _tools/update_graph_snapshot.py --dry-run` prints the local publication workflow.
- [ ] `python _tools/publish_graph_snapshot.py` publishes only allowlisted files when Graphify output exists.
- [ ] No secrets or PHI are committed.
