# Hermes Social Agent

A 24/7, quality-first, self-improving social content agent for LinkedIn, Instagram, and X (Twitter), controlled through Telegram and designed to operate at the lowest practical marginal cost using existing Hermes/EC2/model access.

> **Important Cost Rule**: The architecture is designed for ₹0 marginal cost wherever possible, using existing Hermes/EC2/model access and free/local software. It does not silently switch to paid APIs or services.

## Core Features
- **Quality over volume**: Schedules/publishes 1 primary content idea per day, skipping days if quality gates are not met.
- **Platform-native executions**: Distinct narratives and formatting for LinkedIn, Instagram, and X.
- **Human-readable command centers**: Google Sheets for operations monitoring and Obsidian Markdown for strategic memory.
- **Authoritative machine memory**: Local SQLite transactional database.
- **Telegram Remote Control**: Natural language interaction for scheduling, approvals, and status queries.

## Quickstart (Phase 1 — Repository Scaffold)

### 1. Configure Environment
Copy `.env.example` to `.env` and fill in any required variables:
```bash
cp .env.example .env
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
# or install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### 3. Run CLI
```bash
# Check loaded configuration
python -m hermes_social config

# Check version
python -m hermes_social version

# Run the agent (Phase 1 CLI entry point)
python -m hermes_social run
```

### 4. Run Test Suite
```bash
pytest
```

## Project Structure
```text
hermes-social-agent/
├── docs/                      # Documentation and architecture guides
├── src/hermes_social/         # Core application package
│   ├── config.py              # Configuration loader
│   ├── logging_setup.py       # Structured JSON logging
│   ├── cli.py                 # CLI entry point
│   ├── core/                  # Core domain & state machine
│   ├── db/                    # SQLite database & migrations
│   ├── services/              # Pipeline & business logic
│   ├── adapters/              # Social platforms, Telegram, Sheets
│   ├── creative/              # Pillow/ImageMagick rendering
│   └── integrations/          # External tool integrations
└── tests/                     # Test suite
```
