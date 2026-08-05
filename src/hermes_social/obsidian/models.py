"""Data models for Obsidian vault sync."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VaultSyncResult:
    """Result of syncing the Obsidian vault."""
    files_written: int = 0
    files_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    sync_timestamp: str = ""


@dataclass
class DecisionEntry:
    """A single entry in the decision log."""
    timestamp: str
    category: str
    description: str
    old_value: str
    new_value: str
    reason: str
