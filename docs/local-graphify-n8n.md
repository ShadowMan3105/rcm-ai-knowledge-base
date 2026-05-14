# Local Graphify + Ollama + n8n Operating Model

Purpose: generate the KB graph locally with Ollama, publish only a controlled
snapshot to GitHub, and let cloud AIs read that snapshot without accessing the
local model.

## Architecture

```text
local Docker
|-- existing n8n       # orchestration and scheduled/manual triggers
|-- ollama             # local model API
|-- graphify-runner    # builds Graphify map from governed KB files
`-- qdrant optional    # later RAG/vector memory

GitHub
|-- source KB files
`-- _graph/            # advisory published graph snapshot
```

## Current Environment

The current Docker environment already has n8n:

```text
project: n8n-docker
n8n URL: http://localhost:5800
n8n network: n8n-docker_default
```

Do not start another n8n unless explicitly doing a standalone install.

## Attach Ollama To Existing n8n

Use this command when n8n already exists:

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml up -d ollama
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml exec ollama ollama pull qwen2.5-coder:7b
```

Open n8n:

```text
http://localhost:5800
```

n8n Ollama credential URL:

```text
http://ollama:11434
```

Graphify runner Ollama URL:

```text
http://ollama:11434/v1
```

Recommended Graphify model:

```text
qwen2.5-coder:7b
```

Graphify's Ollama backend may still require an `OLLAMA_API_KEY` environment
variable. This is not a real secret for local Ollama; use the placeholder from
`.env.example`:

```text
OLLAMA_API_KEY=ollama-local
```

If your n8n network has a different name:

```powershell
$env:N8N_DOCKER_NETWORK="<network-name>"
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml up -d ollama
```

## Standalone n8n Mode

Use only if you do not already have n8n:

```bash
cp .env.example .env
docker compose -f compose.local-ai.yml --profile standalone-n8n up -d ollama postgres n8n
docker compose -f compose.local-ai.yml exec ollama ollama pull qwen2.5-coder:7b
```

## Generate The Graph Locally

From the host:

```bash
python _tools/update_graph_snapshot.py --backend ollama
```

For local Ollama, the wrapper serializes semantic chunks with
`--max-concurrency 1` and caps semantic chunks with `--token-budget 4000`
unless you explicitly override those values.

From Docker:

```bash
docker compose -f compose.local-ai.yml -f compose.existing-n8n.yml --profile graphify run --rm graphify-runner
```

For a lighter daily run, process only recent changes:

```bash
python _tools/update_graph_snapshot.py --backend ollama --changed-since "24 hours ago"
```

This writes a recent-change snapshot to `_graph/incremental-latest/` by
default. It should be treated as advisory context for changed files only, not as
a full replacement for `_graph/`.

The incremental default is intentionally small for local Ollama: no protocol
bundle, no index summary, and only changed tooling/schema files. Override with
`--protocol-mode minimal` or `--tooling-mode full` when you need broader
context.

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
graphify-kb-corpus/
graphify-kb-corpus-incremental/
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
