# Graphify Agent Prompt for RCM AI Knowledge Base

Use this only after reading `AGENTS.md`, `READ_PROTOCOL.md`, and `AI_PROTOCOL.md`.

You may use Graphify outputs to navigate the KB faster, but Graphify is advisory only. Do not treat inferred graph edges as verified truth.

Required order:

1. Read `index.json` or the generated corpus summary.
2. Filter by `domain`, `status`, `kind`, and `tags`.
3. Prefer `active` entries over `proposed`; treat `challenged`, `deprecated`, and `superseded` according to protocol.
4. Read the source `meta.json`, `report.md`, and `lessons.md` before acting.
5. Check related `challenges/` and `patches/`.
6. Use Graphify only to find relationships, paths, clusters, and candidate contradictions.
7. Convert substantive graph findings into a challenge, patch, or new KB entry. Do not directly rewrite active entries.

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
