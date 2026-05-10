# RCM AI Knowledge Base

A public repository of strategies, blueprints, and lessons learned from RCM, billing operations, automation, and consulting projects.

**Purpose:** Give any AI agent or human collaborator a verified head start — no hallucinations, no reinventing the wheel.

**What lives here:** Final project reports, decision rationales, confirmed mistakes and their root causes, reusable templates.

**What does NOT live here:** Patient data, PHI, HIPAA-regulated content, credentials, API keys, payer-specific rates, or operational live data.

---

## How to Use This KB (for AI Agents)

1. Fetch `index.json` at repo root — get the full map of entries
2. Filter by `tags` or `domain` relevant to your task
3. Read `report.md` for the strategy/blueprint
4. Read `lessons.md` for mistakes to avoid
5. Use `meta.json` per entry to assess recency and status

---

## Domain Structure

| Folder | What it contains |
|---|---|
| `automations/` | n8n workflows, Monday.com automations, AI agents, API integrations |
| `research/` | Payer analysis, timely filing, taxonomy, NPI, regulatory research |
| `rcm-operations/` | SOPs, onboarding frameworks, biller standards, denial management |
| `billing-config/` | eCW v12 setup, 837P/clearinghouse config, ERA/EFT enrollment |
| `executive-reports/` | Strategic summaries for ownership and management |
| `consulting/` | Advisory engagements, gap analyses, roadmaps |
| `_schema/` | Templates and standards for all entries |

---

## How to Contribute

1. Complete a project or research task
2. AI agent will prompt you at the end of any successful process to approve upload
3. On approval: copy `_schema/report-template.md` and `_schema/lessons-template.md` into the relevant domain folder
4. Fill in `meta.json` using `_schema/meta-schema.json`
5. Submit PR or push directly (contributors with PAT access)

---

## Maintainer
Dr. Seidel — RCM Operations & AI Strategy
