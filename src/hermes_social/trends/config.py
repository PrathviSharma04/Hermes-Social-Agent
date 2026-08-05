"""Trend sources config loader."""

from pathlib import Path
import yaml


def load_sources_config(config_path: Path) -> dict:
    """Load and validate config/sources.yaml."""
    if not config_path.exists():
        raise FileNotFoundError(f"Sources configuration file not found at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    return data or {}
