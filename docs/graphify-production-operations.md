# Graphify Production Operations

This document is mandatory operational context for any AI agent maintaining the
published Graphify snapshot.

## Active Production Path

```yaml
active_runner: "Claude/Sonnet via LiteLLM and AWS Bedrock"
transport: "Graphify ollama backend pointed at LiteLLM OpenAI-compatible endpoint"
model_label: "bedrock:claude-sonnet-4-5"
local_lab_path: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\claude_graphify_lab"
runner_script: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\claude_graphify_lab\\run-kb-graphify.ps1"
repo_root: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\review_graphify_git"
output_path: "_graph/incremental-latest/"
cadence: "every 8 hours"
local_times: ["02:00", "10:00", "18:00"]
changed_since: "8 hours ago"
notification_bridge: "n8n workflow qyt7gkqBX8kfwGtO"
notification_webhook: "http://localhost:5800/webhook/graphify-status-rcm-kb"
slack_message_format: "Graphify activado - ejecucion exitosa|ejecucion fallida - YYYY-MM-DD HH:mm:ss"
```

The old Ollama/qwen production automation is paused, not deleted. Ollama remains
available as fallback/local test infrastructure, but it is not the active
published snapshot runner.

## Run Command

From the lab folder:

```powershell
.\run-kb-graphify.ps1 -ChangedSince "8 hours ago" -TokenBudget 1200 -MaxOutputTokens 8192 -CommitPush
```

The script performs the full operation:

1. Syncs `main` from GitHub when `-CommitPush` is set and refuses to run from a dirty tracked worktree.
2. Runs `python _tools/validate.py`.
3. Rebuilds `index.json`.
4. Builds a strict incremental Graphify corpus.
5. Starts LiteLLM/Sonnet if needed.
6. Runs Graphify against a scratch copy of the corpus, not against raw repo files.
7. Publishes only controlled `_graph/incremental-latest/` files.
8. Runs KB validation and Graphify policy validation.
9. Commits and pushes controlled graph files only.
10. Queues and sends the Slack success notification only after the publish path succeeds.

## Notification Reliability

Slack notification is handled through n8n because Slack credentials already live
there. The runner never stores Slack tokens.

Notification rules:

- Success is queued only after validation, controlled publish, commit, and push complete.
- Failure is queued from the top-level catch block for any exception.
- Slack text remains minimal by design: status and local timestamp only.
- Error details stay local in the notification history file and command logs.
- The n8n workflow must return `ok=true`; otherwise the event stays pending.

Local notification files:

```yaml
pending_queue: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\claude_graphify_lab\\out\\notifications\\pending\\*.json"
sent_archive: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\claude_graphify_lab\\out\\notifications\\sent\\*.json"
history_log: "C:\\Users\\Seide\\Documents\\New project 2\\tasks\\claude_graphify_lab\\out\\notifications\\history.jsonl"
```

Flush pending notifications without running Graphify:

```powershell
.\run-kb-graphify.ps1 -FlushNotificationsOnly
```

Create a controlled test notification without running Graphify:

```powershell
.\run-kb-graphify.ps1 -NotifyOnlyStatus success
.\run-kb-graphify.ps1 -NotifyOnlyStatus failure
```

## Failure Policy

```yaml
validation_failure:
  action: "stop before Graphify"
  publish: false
  slack: "failure"

secret_scan_failure:
  action: "stop before publish"
  publish: false
  slack: "failure"

graphify_no_graph_json:
  action: "stop before publish"
  publish: false
  slack: "failure"

graphify_invalid_json_warnings:
  action: "not automatically fatal if Graphify writes graph.json and validators pass"
  reason: "Graphify can split/retry chunks and keep partial usable results"
  publish: "allowed only after graph.json exists and policy checks pass"

git_dirty_before_run:
  action: "stop"
  reason: "unattended runner must not overwrite human or agent changes"
  slack: "failure"

git_push_rejected_remote_advanced:
  action: "stop without pushing stale graph output"
  recovery: "next scheduled run starts from latest main and rebuilds"
  slack: "failure"

n8n_or_slack_unavailable:
  action: "keep event in pending queue"
  recovery: "hourly notification retry automation flushes pending events"
  graph_publish: "not rolled back if publish already succeeded"
```

## Operator Rules For AI Agents

- Do not edit raw Graphify output into the repo.
- Do not commit `graphify-kb-corpus/`, `graphify-kb-corpus-incremental/`,
  `.graphify-kb-corpus/`, `graphify-out/`, `.graphify/`, or local lab `out/`.
- Do not replace the n8n Slack bridge with new Slack credentials unless the user
  explicitly asks.
- Do not claim a successful production run unless the wrapper reports
  `GRAPHIFY_KB_OK`, validation passed, policy check passed, GitHub push
  succeeded or no commit was needed, and the success notification was sent or
  queued.
- If notification is queued but not sent, report it as a notification delivery
  issue, not as a graph generation failure.
