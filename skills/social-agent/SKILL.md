---
name: social-agent
description: Autonomous social media discovery, research, drafting, and design for LinkedIn and X.
version: 1.0.0
metadata:
  hermes:
    tags: [social, automation, content, marketing]
    category: business
---
# Social Media Agent
Project root: ~/Hermes-Social-Agent
Database: ~/Hermes-Social-Agent/data/hermes.db
Read ~/Hermes-Social-Agent/AGENTS.md before work.

## Commands & Orchestration
When asked to manage, trigger, or debug the social pipeline, use these Python CLI commands from the project root:

1. **Trend Discovery (Phase 1):** `python -m hermes_social.cli discover --commit`
   - Scrapes HackerNews, Dev.to, TechCrunch for trending AI/Dev topics.
2. **Deep Research (Phase 2):** `python -m hermes_social.cli research --all`
   - Researches the discovered topics for factual grounding.
3. **Content Generation (Phase 3):** `python -m hermes_social.cli generate --all`
   - Uses the Brand Voice in Obsidian to draft LinkedIn and X content.
4. **Creative/Design (Phase 4):** `python -m hermes_social.cli design --all`
   - Generates image prompts and pushes the drafts to Telegram for human approval.
5. **Full Pipeline Automation:** `./run_daily.sh`
   - Runs all 4 phases sequentially.

## Database Interaction
If asked for stats, history, or post inspection, query `data/hermes.db` (SQLite):
- **Posts Table (`posts`):** Contains `id`, `topic`, `linkedin_text`, `twitter_text`, `status` (DRAFT, PENDING_APPROVAL, APPROVED, PUBLISHED, REJECTED).
- **Research Table (`research`):** Contains `topic`, `facts`, `urls`.

## Manual Overrides
Never manually change the status of a post to PUBLISHED in the DB unless specifically verifying an out-of-band publish. Let the Telegram bot handle approvals.
