"""Experiments and post assignment database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import ExperimentStatus


class ExperimentRepository:
    """Repository for managing content experiments and assignments in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, exp_data: Dict[str, Any]) -> int:
        """Create a new experiment record and return its ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO experiments (
                name, hypothesis, platform, variable,
                variant_a, variant_b, start_date, end_date,
                minimum_samples, status, confidence, conclusion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_data["name"],
                exp_data["hypothesis"],
                exp_data.get("platform"),
                exp_data["variable"],
                exp_data["variant_a"],
                exp_data["variant_b"],
                exp_data.get("start_date"),
                exp_data.get("end_date"),
                exp_data.get("minimum_samples", 10),
                exp_data.get("status", ExperimentStatus.DRAFT.value),
                exp_data.get("confidence", 0.0),
                exp_data.get("conclusion"),
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, exp_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve an experiment by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM experiments WHERE id = ?", (exp_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_status(
        self, exp_id: int, status: Union[ExperimentStatus, str]
    ) -> None:
        """Update experiment status."""
        status_val = (
            status.value if isinstance(status, ExperimentStatus) else str(status)
        )
        self.conn.execute(
            """
            UPDATE experiments
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status_val, exp_id),
        )

    def assign_post(self, post_id: int, exp_id: int, variant: str) -> int:
        """Assign a post to an experiment variant."""
        cursor = self.conn.execute(
            """
            INSERT INTO post_experiment_assignments (post_id, experiment_id, variant)
            VALUES (?, ?, ?)
            """,
            (post_id, exp_id, variant),
        )
        return int(cursor.lastrowid)

    def get_assignment(
        self, post_id: int, exp_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the variant assignment for a post and experiment."""
        cursor = self.conn.execute(
            """
            SELECT * FROM post_experiment_assignments
            WHERE post_id = ? AND experiment_id = ?
            """,
            (post_id, exp_id),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_active(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """List active experiments, optionally filtered by platform."""
        if platform:
            cursor = self.conn.execute(
                "SELECT * FROM experiments WHERE status = ? AND platform = ? ORDER BY id DESC",
                (ExperimentStatus.ACTIVE.value, platform),
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM experiments WHERE status = ? ORDER BY id DESC",
                (ExperimentStatus.ACTIVE.value,),
            )
        return [dict(row) for row in cursor.fetchall()]
