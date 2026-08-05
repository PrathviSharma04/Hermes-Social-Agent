"""Performance snapshots repository with nullable metrics per Section 8 & 23."""

import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import PerformanceWindow


class PerformanceRepository:
    """Repository for managing performance snapshots in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def upsert_snapshot(
        self,
        post_id: int,
        window: Union[PerformanceWindow, str],
        metrics: Dict[str, Any],
    ) -> int:
        """Insert or update a performance snapshot for a specific time window.

        Unavailable metrics must be passed as None, never 0.
        """
        win_val = window.value if isinstance(window, PerformanceWindow) else str(window)
        other_json = (
            json.dumps(metrics.get("other_metrics"))
            if metrics.get("other_metrics") is not None
            else None
        )

        cursor = self.conn.execute(
            """
            INSERT INTO performance_snapshots (
                post_id, window, impressions, reach, likes,
                comments, shares, saves, clicks, profile_visits,
                follows, reposts, other_metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(post_id, window) DO UPDATE SET
                captured_at = CURRENT_TIMESTAMP,
                impressions = excluded.impressions,
                reach = excluded.reach,
                likes = excluded.likes,
                comments = excluded.comments,
                shares = excluded.shares,
                saves = excluded.saves,
                clicks = excluded.clicks,
                profile_visits = excluded.profile_visits,
                follows = excluded.follows,
                reposts = excluded.reposts,
                other_metrics_json = excluded.other_metrics_json
            """,
            (
                post_id,
                win_val,
                metrics.get("impressions"),  # None if unavailable, not 0
                metrics.get("reach"),
                metrics.get("likes"),
                metrics.get("comments"),
                metrics.get("shares"),
                metrics.get("saves"),
                metrics.get("clicks"),
                metrics.get("profile_visits"),
                metrics.get("follows"),
                metrics.get("reposts"),
                other_json,
            ),
        )
        # For ON CONFLICT updates, lastrowid might be 0, so query ID
        snapshot = self.get_snapshot(post_id, win_val)
        return int(snapshot["id"]) if snapshot else int(cursor.lastrowid)

    def get_snapshot(
        self, post_id: int, window: Union[PerformanceWindow, str]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a specific performance snapshot."""
        win_val = window.value if isinstance(window, PerformanceWindow) else str(window)
        cursor = self.conn.execute(
            "SELECT * FROM performance_snapshots WHERE post_id = ? AND window = ?",
            (post_id, win_val),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_by_post(self, post_id: int) -> List[Dict[str, Any]]:
        """Retrieve all performance snapshots for a post."""
        cursor = self.conn.execute(
            "SELECT * FROM performance_snapshots WHERE post_id = ? ORDER BY id ASC",
            (post_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
