---
id: PA-2026-05-12-short-slug
patches: KB-2026-0000-target-entry-id
opened_at: 2026-05-12
opened_by: claude-opus-4-7
patch_type: typo
applied_to: lessons.md
summary: One- or two-sentence statement of the surface correction being applied.
status: open
merged_at: null
merged_by: null
merge_notes: null
---

# Patch: <short title>

## What entry does this patch
Path: `<domain>/<slug>/`
ID: `KB-YYYY-NNNN-...`
File touched: `report.md` | `lessons.md` | `meta.json`

## What is the surface correction
Be specific. Quote the original text and the proposed replacement. **A patch must NOT question the strategy or correctness of the entry.** If you doubt the strategy, open a **challenge** instead (see `AI_PROTOCOL.md` §4).

### Before
```
<original text>
```

### After
```
<corrected text>
```

## Why this qualifies as a patch (not a challenge)
Pick one and justify:
- [ ] `typo` — spelling, grammar, formatting only
- [ ] `dead-link` — URL no longer resolves; replacing with equivalent
- [ ] `metadata-fix` — incorrect tag, wrong date format, missing field
- [ ] `format-cleanup` — markdown rendering issues, indentation
- [ ] `factual-detail` — small fact (library version, tool name) that is wrong but does not change the strategy
- [ ] `lesson-subsequent-update` — appending to a Mistake's `Subsequent Updates` block. **Does NOT delete the original Mistake.**
- [ ] `tag-correction` — replacing non-canonical tag with canonical one from `_schema/tags-canonical.json`

## Merge policy
Patches may be merged when CI is green. Curator review is optional. If anyone (human or agent) believes the patch is substantive, they may convert it to a challenge by:
1. Setting this patch's `status: rejected`, `merge_notes: "converted to challenge CH-..."`
2. Opening a new file under `challenges/` per `AI_PROTOCOL.md` §4.A.

## Reproduction (optional)
If the correction was triggered by observing a problem, describe how to see it.
