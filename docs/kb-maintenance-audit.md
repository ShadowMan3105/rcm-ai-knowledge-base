# KB Maintenance Audit

Purpose: prevent slow drift in the RCM AI Knowledge Base so future AI agents can
trust the repository map without rediscovering operational context.

## Weekly Automation Contract

```yaml
automation_name: kb-weekly-structure-audit
cadence: weekly
scope: repository health, Graphify integration, machine-readability
mode: read-only unless the user explicitly asks for fixes
```

Required checks:

1. Confirm local `main` and `origin/main` relationship.
2. Run `python _tools/validate.py`.
3. Run `python _tools/check_graphify_policy.py`.
4. Run `python -m compileall _tools`.
5. Check `meta.json.related` values resolve to existing KB IDs or entry paths.
6. Check `ops/graphify/run-kb-graphify.ps1` is still the documented production wrapper.
7. Check Graphify docs agree on:
   - active model;
   - 02:00 local schedule;
   - `24 hours ago` changed-file window;
   - `_graph/incremental-latest/` output;
   - n8n Slack bridge and retry outbox.
8. Check `_graph/*/manifest.json` records an explainable source commit,
   model, backend, graph counts, and source status.
9. Scan tracked operational files for obvious secret patterns.

## Drift Rules

```yaml
wrapper_drift:
  rule: "Production behavior must be inspectable from ops/graphify/."
  fix: "Move or mirror wrapper/config changes into ops/graphify/ and update docs."

related_link_drift:
  rule: "meta.json related contains only existing KB IDs or existing entry paths."
  fix: "Use existing KB IDs, create the missing KB entry, or move external context to report.md."

graph_manifest_drift:
  rule: "source_worktree_status should describe source inputs, not controlled generated outputs."
  fix: "Keep index.json/_graph as controlled output metadata and investigate real source dirtiness."

legacy_stack_drift:
  rule: "Ollama/qwen and Opus paths are fallback or experiment paths unless AGENTS.md says otherwise."
  fix: "Label legacy paths clearly or update them to the active Sonnet production path."

notification_drift:
  rule: "Success and failure notifications must be queued by the wrapper and retried locally."
  fix: "Do not move notification logic into an undocumented script or a second Slack credential."
```

## Expected Weekly Output

The reviewer should report:

- pass/fail status for each required check;
- exact file and line for any drift;
- whether the issue is documentation-only, validator/tooling, Graphify runtime,
  notification delivery, or repository content;
- the smallest safe fix;
- verification evidence after fixes, if fixes were requested.

Do not claim the repo is clean without validator and policy evidence.
