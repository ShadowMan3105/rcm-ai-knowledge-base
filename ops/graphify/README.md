# Graphify Production Runner

This folder is the versioned production boundary for the KB Graphify job.

The active scheduled job runs `run-kb-graphify.ps1` from the repository, not
from an untracked local lab folder. Runtime secrets still stay outside Git in
an env file.

## Required Runtime Inputs

```text
EnvFile: .env-compatible file containing AWS_BEARER_TOKEN_BEDROCK and LITELLM_MASTER_KEY
RepoRoot: repository root containing AGENTS.md and _tools/
NotifyUrl: existing n8n Slack bridge webhook
```

The env file path may be passed with `-EnvFile` or supplied as:

```text
GRAPHIFY_ENV_FILE=<absolute path to local env file>
```

Optional overrides:

```text
GRAPHIFY_LAB_ROOT=<absolute path to this folder or a compatible copied lab>
GRAPHIFY_NOTIFICATION_ROOT=<absolute path to notification outbox>
```

## Production Command

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\graphify\run-kb-graphify.ps1 `
  -EnvFile "<local-env-file>" `
  -ChangedSince "24 hours ago" `
  -TokenBudget 1200 `
  -MaxOutputTokens 8192 `
  -CommitPush
```

## Notification Retry Only

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\graphify\run-kb-graphify.ps1 `
  -FlushNotificationsOnly
```

## Non-Negotiable Rules

- Do not commit env files, local outbox files, raw Graphify output, or Docker
  runtime folders.
- Do not move the production wrapper outside the repo without leaving a
  versioned mirror here and updating `docs/graphify-production-operations.md`.
- Keep success/failure Slack notification behavior in this wrapper; do not
  split it into undocumented local scripts.
- If Graphify fails before publish, queue a failure notification.
- If n8n or Slack is unavailable, preserve the local pending notification file
  for the retry automation.
