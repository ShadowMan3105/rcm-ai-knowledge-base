# Local Graphify + Ollama + n8n Operating Model

Purpose: generate the KB graph locally with Ollama, publish only a controlled
snapshot to GitHub, and let cloud AIs read that snapshot without accessing the
local model.

## Architecture

```text
local Docker
|-- n8n                # orchestration and scheduled/manual triggers
|-- ollama             # local model API
|-- graphify-runner    # builds Graphify map from governed KB files
|-- postgres           # n8n database
`-- qdrant optional    # later RAG/vector memory

GitHub
|-- source KB files
`-- _graph/            # advisory published graph snapshot
```

## Start The Local Stack

```bash
cp .env.example .env
docker compose -f compose.local-ai.yml up -d ollama postgres n8n
docker compose -f compose.local-ai.yml exec ollama ollama pull llama3.1
```

Open n8n:

```text
http://localhost:5678
```

n8n Ollama credential URL:

```text
http://ollama:11434
```

## Generate The Graph Locally

From the host:

```bash
python _tools/update_graph_snapshot.py --backend ollama
```

From Docker:

```bash
docker compose -f compose.local-ai.yml --profile graphify run --rm graphify-runner
```

## Publish The Graph Snapshot

Use this when the local graph output looks correct and Git credentials are
available:

```bash
python _tools/update_graph_snapshot.py --backend ollama --commit --push
```

This commits only:

```text
_graph/README.md
_graph/GRAPH_REPORT.md
_graph/graph.json
_graph/manifest.json
index.json
```

Raw local files stay ignored:

```text
.graphify-kb-corpus/
graphify-out/
.graphify/
.graphify_cache/
.graphify_labels.json
```

## n8n Trigger Options

Recommended first workflow:

```text
Manual Trigger
-> Execute Command or local webhook runner
-> python _tools/update_graph_snapshot.py --backend ollama --commit --push
-> notify result
```

Safer production workflow:

```text
Schedule Trigger
-> Git pull main
-> run graph update
-> if git diff _graph/ exists, commit and push
-> send success/failure notification
```

Do not expose Ollama to the public internet. If remote execution is needed,
move the full stack to a private VPS or use a private VPN/tunnel with explicit
authentication.

## Cloud AI Read Contract

Cloud AIs read GitHub only:

1. `AGENTS.md`
2. `READ_PROTOCOL.md`
3. `AI_PROTOCOL.md`
4. `index.json`
5. `_graph/GRAPH_REPORT.md` when present
6. `_graph/graph.json` for navigation only
7. source KB files for verification

They never call local Ollama directly.
