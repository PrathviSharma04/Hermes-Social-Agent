"""Creative assets database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import QAStatus


class AssetRepository:
    """Repository for managing creative assets in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, asset_data: Dict[str, Any]) -> int:
        """Create a new asset record and return its ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO assets (
                post_id, asset_type, path, width, height,
                checksum, generation_method, prompt_reference,
                design_system, qa_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_data["post_id"],
                asset_data["asset_type"],
                asset_data["path"],
                asset_data.get("width"),
                asset_data.get("height"),
                asset_data.get("checksum"),
                asset_data.get("generation_method"),
                asset_data.get("prompt_reference"),
                asset_data.get("design_system"),
                asset_data.get("qa_status", QAStatus.PENDING.value),
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve an asset by ID."""
        cursor = self.conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_by_post(self, post_id: int) -> List[Dict[str, Any]]:
        """Retrieve all assets associated with a post."""
        cursor = self.conn.execute(
            "SELECT * FROM assets WHERE post_id = ? ORDER BY id ASC", (post_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_qa_status(
        self, asset_id: int, qa_status: Union[QAStatus, str]
    ) -> None:
        """Update QA status of an asset."""
        status_val = (
            qa_status.value if isinstance(qa_status, QAStatus) else str(qa_status)
        )
        self.conn.execute(
            "UPDATE assets SET qa_status = ? WHERE id = ?",
            (status_val, asset_id),
        )
