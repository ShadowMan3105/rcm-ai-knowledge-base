# Lessons Learned - Denied Claims Refresh With Supabase Authority, Monday Resolution, And Cache Rebuild

## Mistakes Made

### Mistake 1: Starting a KB write from a stale local copy instead of the current remote state
- **Category:** `process`
- **Severity:** `high`
- **What happened:** A first attempt began creating a KB entry from the local checkout before proving that it matched the current remote `main` and before checking open PRs that could reserve the next KB ID.
- **Root cause:** Local repo availability was treated as enough evidence of current KB state.
- **How it was caught:** The user corrected the workflow and required read-copy-change-upload against the current GitHub state.
- **Fix applied:** GitHub authentication was repaired, remote `main` was fetched, a new branch was created from `origin/main`, open PRs were inspected, and the entry ID was chosen to avoid a pending PR collision.
- **Rule extracted:** Before writing to the KB, always read the current remote state, inspect open PRs for pending IDs or related edits, then branch from that current state. Never create a new KB entry from an unverified local snapshot.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 2: Creating local KB scaffolding before GitHub write access was verified
- **Category:** `process`
- **Severity:** `medium`
- **What happened:** An empty entry folder was created locally while GitHub authentication was still invalid.
- **Root cause:** Local preparation started before the publish path was proven.
- **How it was caught:** Git status and folder inspection showed an empty attempted folder while both the GitHub connector and `gh` authentication were invalid.
- **Fix applied:** The empty folder was removed, GitHub CLI authentication was repaired, and the correct workflow restarted from fetched remote `main`.
- **Rule extracted:** Verify repository access and current remote state before creating KB files. If a failed attempt leaves local scaffolding, remove it before restarting the write flow.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 3: Assuming Monday board columns existed from memory
- **Category:** `api-integration`
- **Severity:** `high`
- **What happened:** A controlled Monday update attempted to write fields for date of birth and payer using column IDs that were not present on the live Denials board.
- **Root cause:** A mapping borrowed from prior patterns was not constrained to the live board columns proven in the current run.
- **How it was caught:** Monday mutations failed with invalid column ID errors.
- **Fix applied:** The absent fields were removed from the direct update payload, live Monday state was re-read, and the run continued idempotently without creating duplicate items.
- **Rule extracted:** Never assume Monday column IDs from prior scripts or memory. Build write payloads only from columns proven on the current board, and treat invalid-column errors as a stop-and-re-read event.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 4: Letting partial Monday success create a risk of duplicate items
- **Category:** `process`
- **Severity:** `high`
- **What happened:** A write run created new Monday denial items before a later mutation failed on an invalid column mapping.
- **Root cause:** The first write sequence did not fail before all external mutations; therefore, rerunning naively could have created duplicates.
- **How it was caught:** A post-error dry-run showed the new Monday items already existed while Supabase still needed corresponding rows.
- **Fix applied:** The runner was adjusted to re-read Monday, classify already-created items as existing links, then insert the missing Supabase rows and continue updates/resolutions.
- **Rule extracted:** Bulk external writes must be resumable. After any partial failure, re-read live state and continue from the new ledger rather than replaying the original plan.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 5: Treating an append-only Data Table interface as if it could refresh a cache
- **Category:** `strategy`
- **Severity:** `medium`
- **What happened:** The available n8n MCP Data Table tools exposed row insertion and table/column changes, but not row update/delete needed to refresh the existing denial cache cleanly.
- **Root cause:** The cache was initially considered refreshable before checking the exact tool capabilities available in the current environment.
- **How it was caught:** Tool discovery showed support for adding rows and table metadata operations but not in-place row refresh or deletion.
- **Fix applied:** The old denial cache was archived by renaming it, and a new versioned cache was created and loaded from verified Supabase current rows.
- **Rule extracted:** If a cache cannot be refreshed cleanly with the available tools, archive it and create a fresh versioned cache from the durable source. Never append duplicate rows to stale cache data.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

### Mistake 6: Trusting a GitHub connector after its token had expired
- **Category:** `configuration`
- **Severity:** `medium`
- **What happened:** The GitHub connector and local `gh` CLI initially returned invalid-token errors, blocking the proper read-copy-change-upload workflow.
- **Root cause:** Authentication freshness was not checked before planning the KB publish.
- **How it was caught:** Both the connector read attempt and `gh auth status` reported invalidated tokens.
- **Fix applied:** GitHub CLI authentication was refreshed, then `gh auth status`, `git fetch`, and open PR inspection were used to prove the publish path was usable.
- **Rule extracted:** For KB publishing, verify GitHub authentication with the connector or `gh auth status` before editing. If the connector is invalid but CLI works, use CLI for fetch, branch, commit, push, and PR.
- **Subsequent Updates:** *(append-only; remove this line once first update is added)*

## Assumptions That Were Wrong

The first wrong assumption was that a local KB checkout represented the latest source of truth. The correct source is remote `main` plus any open PRs that may reserve IDs or contain related work.

The second wrong assumption was that Monday Denials board columns matched earlier script mappings. Live board schemas can drift, and write payloads must be based on current proof.

The third wrong assumption was that an existing n8n cache should be refreshed in place. When only append operations are available, a clean versioned rebuild is safer and more truthful than appending to stale rows.

## What to Do Differently Next Time

Start by checking GitHub auth, fetching remote `main`, and inspecting open PRs. Do not write KB files until that succeeds.

Treat every production denied-claim refresh as a ledgered operation: parse, scope, dry-run, backup, write, re-read, and only then call it complete.

Make every external write idempotent. If a failure happens after some external mutations, re-read and continue from live state.

For n8n caches, prefer update/delete refresh only when the tool supports it. Otherwise, version the cache with an archive-and-create pattern.

## Warnings for Future AI Agents

Do not include PHI, raw claim numbers, credentials, or live board IDs in this KB entry. Keep exact operational evidence in local task outputs, not in the general knowledge base.

Do not use an old local checkout to decide KB IDs. Check remote `main` and open PRs first.

Do not trust stale n8n caches for production writes. Use live Supabase and Monday re-reads for write decisions.

Do not delete raw audit history during an operational denial refresh. Only current operational rows are cleanup candidates unless the user explicitly approves audit retention work.
