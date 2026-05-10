# RCM AI Knowledge Base — Setup & Architecture

## Summary
Designed and deployed a public GitHub repository (`rcm-ai-knowledge-base`) to serve as a persistent, AI-readable knowledge base for RCM operations. The KB stores verified strategies, blueprints, and lessons learned from completed projects so any future AI agent or human collaborator can get a head start without repeating past mistakes.

## Context
After multiple complex projects (n8n automations, payer research, eCW config, Monday.com architecture), valuable knowledge was being lost between sessions. Each new AI conversation started from zero. This KB solves that by creating a structured, version-controlled repository that any AI can query before starting work.

## Approach / Strategy

1. Evaluated three repo architectures (monorepo, multi-repo hub, monorepo + machine-readable index)
2. Selected **Option C** — monorepo with `index.json` for AI navigation + human-readable markdown
3. Defined domain structure based on actual project history
4. Built all templates and schema before creating the repo
5. Kept PAT auth simple (classic token, `repo` scope only) — no OAuth, no webhooks, no CI
6. Excluded n8n from write access — KB is for thinking outputs only, not operational data
7. Pushed structure first, seed content only after structure was validated
8. Created a universal AI upload prompt to trigger KB saves at end of any successful process

## Final Blueprint

### Repo Structure
```
rcm-ai-knowledge-base/
├── README.md                    # Human index
├── index.json                   # Machine-readable map for AI navigation
├── SETUP.md                     # GitHub + PAT setup instructions
├── _schema/
│   ├── report-template.md       # Blueprint template
│   ├── lessons-template.md      # Mistakes template
│   ├── meta-schema.json         # Entry metadata schema
│   └── ai-upload-prompt.md      # Universal prompt for AI agents
├── automations/_index.md
├── research/_index.md
├── rcm-operations/_index.md
├── billing-config/_index.md
├── executive-reports/_index.md
└── consulting/_index.md
```

### AI Navigation Pattern
1. Fetch `index.json` → get domain map
2. Filter by `tags` or `domain`
3. Read `report.md` → strategy/blueprint
4. Read `lessons.md` → mistakes to avoid
5. Check `meta.json` → recency and status

### Upload Flow
- AI detects process completion → presents upload offer
- User replies YES / NO / EDIT
- On YES: AI generates report.md + lessons.md + meta.json from templates
- Files committed to GitHub via PAT
- PAT revoked and regenerated after each use (security practice)

## Results / Verification
- Repo live at: https://github.com/ShadowMan3105/rcm-ai-knowledge-base
- 13 files pushed in initial commit to `main` branch
- All domain folders present and verified
- Upload prompt deployed to Claude Project Instructions

## Reusable Components
- `_schema/report-template.md` — copy for any new entry
- `_schema/lessons-template.md` — copy for any new entry
- `_schema/meta-schema.json` — validate entry metadata
- `_schema/ai-upload-prompt.md` — paste into any AI system prompt

## Related Entries
_None yet — first entry._

## Tags
github, knowledge-base, ai-agents, blueprints, lessons, index, architecture

## Date
2026-05

## Status
production
