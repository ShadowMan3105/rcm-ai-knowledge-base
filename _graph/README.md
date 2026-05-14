# Published Graph Snapshot

This folder is the controlled public snapshot location for Graphify output.

Local Docker/Ollama jobs publish only these files here:

- `GRAPH_REPORT.md`
- `graph.json`
- `manifest.json`
- `README.md`

Raw Graphify working folders stay local and ignored:

- `.graphify-kb-corpus/`
- `graphify-out/`
- `.graphify/`
- `.graphify_cache/`
- `.graphify_labels.json`

AI agents may use `_graph/` for navigation only. They must verify every
conclusion against the authoritative KB files before acting.
