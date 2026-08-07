# Hermes Social Agent
## Pipelines
LINKEDIN = professional networking/brand building/career/industry insights.
X (TWITTER) = real-time tech/news/short-form thought leadership.

## Discovery & Research Rule
The Social Agent brain runs in two steps:
1. Discovering trends (using TechCrunch, HackerNews, Dev.to).
2. Deep Research on the chosen topic before drafting.
Always verify facts and never hallucinate. Keep the context accurate.

## Database
Source of truth: ~/Hermes-Social-Agent/data/hermes.db (SQLite)
Settings/Auth: ~/Hermes-Social-Agent/.env

## Autonomy & Telemetry
Default post status is DRAFT.
DRAFT means research, generate, design, and wait for human approval in Telegram.
Posts only go LIVE when the human clicks "Approve" via the Telegram Commander.

## Automation Pipeline
The entire process from discovery to Telegram approval is fully orchestrated. 
If diagnosing or managing this agent, use the pre-built CLI commands (`python -m hermes_social.cli ...`) rather than raw python scripts when possible.
