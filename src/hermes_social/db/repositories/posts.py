"""Post database repository with idempotency key enforcement."""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import PostStatus
from hermes_social.core.state_machine import validate_post_transition


class PostRepository:
    """Repository for managing social media posts in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, post_data: Dict[str, Any]) -> int:
        """Create a new post record and enforce idempotency_key uniqueness."""
        idempotency_key = post_data.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("idempotency_key is required when creating a post.")

        cursor = self.conn.execute(
            """
            INSERT INTO posts (
                content_idea_id, platform, format, master_post_id,
                version, hook, body, cta, hashtags, word_count,
                slide_count, brand_score, quality_score, approval_status,
                scheduled_at, published_at, platform_post_id, platform_url,
                status, idempotency_key
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                post_data["content_idea_id"],
                post_data["platform"],
                post_data["format"],
                post_data.get("master_post_id"),
                post_data.get("version", 1),
                post_data.get("hook"),
                post_data["body"],
                post_data.get("cta"),
                post_data.get("hashtags"),
                post_data.get("word_count", 0),
                post_data.get("slide_count", 0),
                post_data.get("brand_score", 0.0),
                post_data.get("quality_score", 0.0),
                post_data.get("approval_status", "REQUIRED"),
                post_data.get("scheduled_at"),
                post_data.get("published_at"),
                post_data.get("platform_post_id"),
                post_data.get("platform_url"),
                post_data.get("status", PostStatus.DRAFT.value),
                idempotency_key,
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a post by ID."""
        cursor = self.conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a post by its unique idempotency key."""
        cursor = self.conn.execute(
            "SELECT * FROM posts WHERE idempotency_key = ?", (key,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_status(self, post_id: int, new_status: Union[PostStatus, str]) -> None:
        """Update post status after validating transition rules."""
        post = self.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        current_status = post["status"]
        validate_post_transition(current_status, new_status)

        target_status = (
            new_status.value if isinstance(new_status, PostStatus) else str(new_status)
        )
        self.conn.execute(
            """
            UPDATE posts
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (target_status, post_id),
        )

    def get_recent_posts(self, days: int = 30) -> List[Dict[str, Any]]:
        """Retrieve recent posts from the database."""
        cursor = self.conn.execute(
            """
            SELECT * FROM posts 
            WHERE created_at >= date('now', '-' || ? || ' days')
            ORDER BY created_at DESC
            """,
            (days,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_by_status(self, status: Union[PostStatus, str]) -> List[Dict[str, Any]]:
        """List posts matching a specific status."""
        status_val = status.value if isinstance(status, PostStatus) else str(status)
        cursor = self.conn.execute(
            "SELECT * FROM posts WHERE status = ? ORDER BY id DESC",
            (status_val,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def list_scheduled(
        self, start: datetime, end: datetime
    ) -> List[Dict[str, Any]]:
        """List scheduled posts within a given time range."""
        cursor = self.conn.execute(
            """
            SELECT * FROM posts
            WHERE status = ? AND scheduled_at BETWEEN ? AND ?
            ORDER BY scheduled_at ASC
            """,
            (PostStatus.SCHEDULED.value, start.isoformat(), end.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def mark_published(
        self, post_id: int, platform_post_id: str, platform_url: str
    ) -> None:
        """Mark a post as published and record external platform reference IDs."""
        post = self.get_by_id(post_id)
        if not post:
            raise ValueError(f"Post {post_id} not found.")

        validate_post_transition(post["status"], PostStatus.PUBLISHED)

        self.conn.execute(
            """
            UPDATE posts
            SET status = ?, published_at = CURRENT_TIMESTAMP,
                platform_post_id = ?, platform_url = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                PostStatus.PUBLISHED.value,
                platform_post_id,
                platform_url,
                post_id,
            ),
        )
