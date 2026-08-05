"""Content idea database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import ContentIdeaStatus
from hermes_social.core.state_machine import validate_content_idea_transition


class ContentIdeaRepository:
    """Repository for managing content ideas in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, idea_data: Dict[str, Any]) -> int:
        """Create a new content idea record and return its ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO content_ideas (
                topic_id, angle, audience_problem, core_value,
                format_recommendation, originality_score, brand_fit_score,
                information_value_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                idea_data["topic_id"],
                idea_data["angle"],
                idea_data.get("audience_problem"),
                idea_data.get("core_value"),
                idea_data.get("format_recommendation"),
                idea_data.get("originality_score", 0.0),
                idea_data.get("brand_fit_score", 0.0),
                idea_data.get("information_value_score", 0.0),
                idea_data.get("status", ContentIdeaStatus.DRAFT.value),
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, idea_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a content idea by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM content_ideas WHERE id = ?", (idea_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_status(
        self, idea_id: int, new_status: Union[ContentIdeaStatus, str]
    ) -> None:
        """Update content idea status after validating transition rules."""
        idea = self.get_by_id(idea_id)
        if not idea:
            raise ValueError(f"Content Idea {idea_id} not found.")

        current_status = idea["status"]
        validate_content_idea_transition(current_status, new_status)

        target_status = (
            new_status.value
            if isinstance(new_status, ContentIdeaStatus)
            else str(new_status)
        )
        self.conn.execute(
            """
            UPDATE content_ideas
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target_status, idea_id),
        )

    def list_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """List all content ideas created for a topic."""
        cursor = self.conn.execute(
            "SELECT * FROM content_ideas WHERE topic_id = ? ORDER BY id DESC",
            (topic_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
