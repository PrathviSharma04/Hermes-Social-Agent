"""Obsidian Vault Sync for Strategy Rules."""

import logging
import sqlite3
from pathlib import Path
from hermes_social.config import AppConfig

logger = logging.getLogger(__name__)


def generate_confidence_meter(confidence: float) -> str:
    """Generates a visual meter like 🟩🟩🟩⬜⬜ for Obsidian."""
    filled = int(confidence * 5)
    return ("🟩" * filled) + ("⬜" * (5 - filled))


def sync_vault(conn: sqlite3.Connection, config: AppConfig) -> None:
    """
    Dumps strategy rules into the Obsidian Vault for human reading.
    """
    strategy_dir = Path(config.obsidian_vault_path) / "Strategy"
    strategy_dir.mkdir(parents=True, exist_ok=True)
    
    cursor = conn.execute("SELECT * FROM strategy_rules")
    rules = cursor.fetchall()
    
    logger.info(f"Syncing {len(rules)} strategy rules to Obsidian.")
    
    for row in rules:
        rule_id = row["id"]
        platform = row["platform"]
        status = row["status"]
        confidence = row["confidence"]
        meter = generate_confidence_meter(confidence)
        
        filename = strategy_dir / f"Rule_{rule_id}_{platform}.md"
        
        content = f"""---
id: {rule_id}
platform: {platform}
status: {status}
confidence: {confidence:.2f}
last_validated: {row['last_validated_at']}
---

# {platform.capitalize()} Strategy Rule {rule_id}

**Status:** {status}
**Confidence:** {meter} ({confidence:.0%})

## The Rule
> {row['rule']}

## Evidence Summary
{row['evidence_summary']}

## Sample Size
{row['sample_size']} posts evaluated.
"""
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
            
    logger.info("Obsidian Strategy sync complete.")
