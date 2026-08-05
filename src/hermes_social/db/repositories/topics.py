"""Topic and TopicSource database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import TopicStatus
from hermes_social.core.state_machine import validate_topic_transition


class TopicRepository:
    """Repository for managing topics and topic_sources in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, topic_data: Dict[str, Any]) -> int:
        """Create a new topic record and return its ID."""
        cursor = self.conn.execute(
            """
            INSERT INTO topics (
                canonical_topic, summary, category, content_pillar,
                trend_velocity, audience_relevance, saturation_score,
                unique_angle_score, visual_potential, source_authority,
                opportunity_score, status, rejection_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic_data["canonical_topic"],
                topic_data.get("summary"),
                topic_data.get("category"),
                topic_data.get("content_pillar"),
                topic_data.get("trend_velocity", 0.0),
                topic_data.get("audience_relevance", 0.0),
                topic_data.get("saturation_score", 0.0),
                topic_data.get("unique_angle_score", 0.0),
                topic_data.get("visual_potential", 0.0),
                topic_data.get("source_authority", 0.0),
                topic_data.get("opportunity_score", 0.0),
                topic_data.get("status", TopicStatus.DISCOVERED.value),
                topic_data.get("rejection_reason"),
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a topic by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM topics WHERE id = ?", (topic_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_status(
        self, topic_id: int, new_status: Union[TopicStatus, str]
    ) -> None:
        """Update topic status after validating transition rules."""
        topic = self.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found.")

        current_status = topic["status"]
        validate_topic_transition(current_status, new_status)

        target_status = (
            new_status.value if isinstance(new_status, TopicStatus) else str(new_status)
        )
        self.conn.execute(
            """
            UPDATE topics
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target_status, topic_id),
        )

    def list_by_status(
        self, status: Union[TopicStatus, str]
    ) -> List[Dict[str, Any]]:
        """List topics with a specific status."""
        status_val = status.value if isinstance(status, TopicStatus) else str(status)
        cursor = self.conn.execute(
            "SELECT * FROM topics WHERE status = ? ORDER BY id DESC",
            (status_val,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_top_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List top scoring non-rejected, non-archived topic candidates."""
        cursor = self.conn.execute(
            """
            SELECT * FROM topics
            WHERE status NOT IN ('REJECTED', 'ARCHIVED')
            ORDER BY opportunity_score DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_source(self, topic_id: int, source_data: Dict[str, Any]) -> int:
        """Add a discovered source for a topic."""
        cursor = self.conn.execute(
            """
            INSERT INTO topic_sources (
                topic_id, source_type, source_name, url,
                published_at, authority_score, raw_excerpt_hash, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                topic_id,
                source_data["source_type"],
                source_data["source_name"],
                source_data.get("url"),
                source_data.get("published_at"),
                source_data.get("authority_score", 0.0),
                source_data.get("raw_excerpt_hash"),
                source_data.get("notes"),
            ),
        )
        return int(cursor.lastrowid)

    def get_sources(self, topic_id: int) -> List[Dict[str, Any]]:
        """Retrieve all sources linked to a topic."""
        cursor = self.conn.execute(
            "SELECT * FROM topic_sources WHERE topic_id = ? ORDER BY authority_score DESC",
            (topic_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
