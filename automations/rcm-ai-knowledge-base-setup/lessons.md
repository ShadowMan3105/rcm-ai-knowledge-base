# Lessons Learned — RCM AI Knowledge Base Setup

## Mistakes Made

### Mistake 1: PAT shared in chat message
- **What happened:** GitHub Personal Access Token was pasted directly into the conversation to authorize the push
- **Root cause:** No pre-established secure credential handoff method
- **How it was caught:** Recognized immediately after push completed
- **Fix applied:** User instructed to revoke token immediately and generate a new one
- **Rule extracted:** Never leave a PAT active after sharing it in any chat interface. Revoke within minutes of use. Store only in a password manager.

### Mistake 2: Domain folder _index.md files failed on first bash attempt
- **What happened:** Loop script tried to write to folders before they existed
- **Root cause:** `mkdir -p` and file write were in separate commands; shell used `/bin/sh` not `/bin/bash`, causing heredoc syntax failure
- **Fix applied:** Separated mkdir and echo commands; used simple echo redirection instead of heredoc
- **Rule extracted:** Always verify directory exists before writing files in shell scripts. Test with `/bin/sh` compatibility when bash is not guaranteed.

---

## Assumptions That Were Wrong
- Assumed bash heredoc syntax would work in the container shell — it did not (`/bin/sh` was used)
- Assumed folder creation and file write could be reliably chained in one loop — required separation

## What to Do Differently Next Time
- Pre-establish a secure PAT handoff method (e.g. environment variable, password manager share) before starting any GitHub push task
- Test shell scripts with `/bin/sh` compatibility or explicitly invoke `/bin/bash`
- Always run `find . -type f | sort` to verify structure before committing

## Warnings for Future AI Agents
- Never store or reuse a PAT that was shared in a chat message — treat it as compromised immediately after use
- When writing files in loops in bash_tool, do not assume bash heredoc works — use simple echo or create_file tool instead
- Do not push seed content to a KB repo until the structure has been reviewed and approved by the user
- index.json `entries` array starts empty — do not hallucinate entries that don't exist yet
