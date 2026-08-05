"""Vault initialization and folder structure."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Standard folders for the Obsidian vault
VAULT_FOLDERS = [
    "00-Dashboard",
    "01-Research",
    "02-Strategy-Rules",
    "03-Experiments",
    "04-Decision-Log"
]

README_CONTENT = """# Hermes Social Agent Vault

This Obsidian vault is the human-readable strategy memory and dashboard for the Hermes Social Agent. 
It is **automatically generated** from the SQLite database.

## Structure

- **00-Dashboard**: Monthly performance reviews and high-level metrics.
- **01-Research**: Knowledge packs and facts extracted from discovering topics.
- **02-Strategy-Rules**: Platform-specific rules learned from experiments or pre-configured.
- **03-Experiments**: Details of active and completed A/B tests.
- **04-Decision-Log**: Audit log of significant strategy changes.

> [!WARNING]
> Do not store API keys or secrets in this vault.
> This vault is designed to be a one-way mirror of the agent's internal state.
"""

def initialize_vault(vault_path: Path) -> None:
    """
    Creates the full folder structure for the Obsidian vault.
    Idempotent: safe to call multiple times.
    """
    try:
        vault_path.mkdir(parents=True, exist_ok=True)
        
        for folder in VAULT_FOLDERS:
            folder_path = vault_path / folder
            folder_path.mkdir(exist_ok=True)
            
        readme_path = vault_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(README_CONTENT, encoding="utf-8")
            
        logger.info(f"Obsidian vault initialized at {vault_path}")
    except Exception as e:
        logger.error(f"Failed to initialize vault at {vault_path}: {e}")
        raise
