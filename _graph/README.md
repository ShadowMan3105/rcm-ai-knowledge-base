# Published Graph Snapshot

This folder is a controlled, commit-safe Graphify snapshot generated from the
RCM AI Knowledge Base.

Read order for AI agents:

1. `AGENTS.md`
2. `READ_PROTOCOL.md`
3. `AI_PROTOCOL.md`
4. `index.json`
5. `_graph/GRAPH_REPORT.md`
6. `_graph/graph.json` only for navigation
7. Source `meta.json`, `report.md`, `lessons.md`, `challenges/`, and `patches/`

Rules:

- `_graph/` is advisory only.
- Do not treat inferred graph edges as KB truth.
- Do not edit active KB entries based only on graph output.
- Convert substantive graph findings into a challenge, patch, or governed KB entry.
- Raw `graphify-kb-corpus/`, `.graphify-kb-corpus/`, and `graphify-out/` stay local and ignored.
