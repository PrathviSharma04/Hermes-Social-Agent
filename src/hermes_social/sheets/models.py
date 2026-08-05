"""Data models for Google Sheets sync."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TabSyncResult:
    """Result of syncing a single tab."""
    tab_name: str
    rows_synced: int = 0
    status: str = "PENDING"  # SUCCESS, FAILED, SKIPPED
    error_message: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class SyncResult:
    """Overall result of a Google Sheets sync operation."""
    overall_status: str = "PENDING"
    tab_results: List[TabSyncResult] = field(default_factory=list)
    sync_timestamp: str = ""
    total_duration_ms: float = 0.0
