# Graphify Agent Prompt for RCM AI Knowledge Base

Use this only after reading `AGENTS.md`, `READ_PROTOCOL.md`, and `AI_PROTOCOL.md`.

You may use Graphify outputs to navigate the KB faster, but Graphify is advisory only. Do not treat inferred graph edges as verified truth.

Required order:

1. Read `AGENTS.md`, `READ_PROTOCOL.md`, `AI_PROTOCOL.md`, and `index.json`.
2. If `_graph/GRAPH_REPORT.md` exists, read it as an advisory map.
3. If the task depends on recent repository changes, read `_graph/incremental-latest/GRAPH_REPORT.md`.
4. Use `_graph/graph.json`, `_graph/incremental-latest/graph.json`, or Graphify queries only to find relationships, paths, clusters, and candidate contradictions.
5. Filter source entries by `domain`, `status`, `kind`, and `tags`.
6. Prefer `active` entries over `proposed`; treat `challenged`, `deprecated`, and `superseded` according to protocol.
7. Read the source `meta.json`, `report.md`, and `lessons.md` before acting.
8. Check related `challenges/` and `patches/`.
9. Convert substantive graph findings into a challenge, patch, or new KB entry. Do not directly rewrite active entries.

Safe example questions:

```text
What entries connect denial management, eCW setup, and automation risk?
Which active entries mention payer enrollment and also connect to billing configuration?
What open challenges may affect an automation decision?
Which lessons repeat across consulting and rcm-operations?
```

Unsafe behavior:

```text
Do not change an active report because Graphify inferred a contradiction.
Do not delete or rewrite a Mistake block.
Do not add PHI, credentials, payer-specific rates, or live operational data to the graph.
Do not bypass validate.py or rebuild_index.py.
```
