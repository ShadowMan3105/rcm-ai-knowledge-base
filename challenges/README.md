# Challenges

Open and resolved challenges against active KB entries.

**Do not edit an active entry's `report.md` or `lessons.md` directly.** If you believe an entry is wrong, obsolete, or incomplete, open a challenge here.

## How to open a challenge

1. Copy `_schema/challenge-template.md` to `challenges/CH-YYYY-MM-DD-short-slug.md`.
2. Fill in the frontmatter (`challenges:` is the target entry's `id`).
3. In the target entry's `meta.json`:
   - Add your challenge ID to `challenged_by`.
   - Set `status` to `challenged`.
4. Run `python _tools/validate.py` and `python _tools/rebuild_index.py`.
5. Commit with message: `challenge(KB-XXXX-XXXX-...): <one-line reason>`.

See [AI_PROTOCOL.md](../AI_PROTOCOL.md) §4 and §7 for the full rules.

## Lifecycle

```
open ──► (accepted | rejected | partial)
```

Only the curator (Dr. Seidel) — or an agent acting under explicit in-session authorization — may resolve a challenge.
