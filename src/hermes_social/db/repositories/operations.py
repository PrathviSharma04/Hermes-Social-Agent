"""Operational audit and background task repositories."""

import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import ScheduledActionStatus, SystemEventLevel


class OperationsRepository:
    """Repository for scheduled actions, Telegram audit log, model run logs, and system events."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_scheduled_action(self, action_data: Dict[str, Any]) -> int:
        """Create a scheduled action with idempotency key enforcement."""
        idempotency_key = action_data.get("idempotency_key")
        if not idempotency_key:
            raise ValueError("idempotency_key is required for scheduled actions.")

        cursor = self.conn.execute(
            """
            INSERT INTO scheduled_actions (
                action_type, payload_json, scheduled_for, status, idempotency_key
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                action_data["action_type"],
                action_data["payload_json"],
                action_data["scheduled_for"],
                action_data.get("status", ScheduledActionStatus.PENDING.value),
                idempotency_key,
            ),
        )
        return int(cursor.lastrowid)

    def get_scheduled_action_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a scheduled action by its unique idempotency key."""
        cursor = self.conn.execute(
            "SELECT * FROM scheduled_actions WHERE idempotency_key = ?", (key,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_pending_scheduled_actions(
        self, before_time: datetime
    ) -> List[Dict[str, Any]]:
        """Retrieve all PENDING scheduled actions scheduled on or before before_time."""
        cursor = self.conn.execute(
            """
            SELECT * FROM scheduled_actions
            WHERE status = ? AND scheduled_for <= ?
            ORDER BY scheduled_for ASC
            """,
            (ScheduledActionStatus.PENDING.value, before_time.isoformat()),
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_scheduled_action_status(
        self, action_id: int, status: Union[ScheduledActionStatus, str]
    ) -> None:
        """Update status of a scheduled action."""
        status_val = (
            status.value
            if isinstance(status, ScheduledActionStatus)
            else str(status)
        )
        self.conn.execute(
            """
            UPDATE scheduled_actions
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status_val, action_id),
        )

    def log_telegram_command(
        self,
        chat_id: str,
        raw_text: str,
        parsed_intent: Optional[str] = None,
        result_action: Optional[str] = None,
        result_status: Optional[str] = None,
    ) -> int:
        """Audit log an incoming Telegram command and its resulting action."""
        cursor = self.conn.execute(
            """
            INSERT INTO telegram_commands (
                chat_id, raw_text, parsed_intent, result_action, result_status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, raw_text, parsed_intent, result_action, result_status),
        )
        return int(cursor.lastrowid)

    def log_model_run(
        self,
        task_type: str,
        model_route: str,
        success: bool,
        retry_count: int = 0,
        quality_score: Optional[float] = None,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
    ) -> int:
        """Log an LLM model invocation for observability and auditing."""
        cursor = self.conn.execute(
            """
            INSERT INTO model_runs (
                task_type, model_route, success, retry_count,
                quality_score, tokens_used, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_type,
                model_route,
                1 if success else 0,
                retry_count,
                quality_score,
                tokens_used,
                error,
            ),
        )
        return int(cursor.lastrowid)

    def log_system_event(
        self,
        level: Union[SystemEventLevel, str],
        category: str,
        message: str,
        context_json: Optional[str] = None,
    ) -> int:
        """Log a system event to the operational audit trail."""
        lvl_val = (
            level.value if isinstance(level, SystemEventLevel) else str(level)
        )
        cursor = self.conn.execute(
            """
            INSERT INTO system_events (level, category, message, context_json)
            VALUES (?, ?, ?, ?)
            """,
            (lvl_val, category, message, context_json),
        )
        return int(cursor.lastrowid)

    def list_system_events(
        self, limit: int = 50, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent system events."""
        if category:
            cursor = self.conn.execute(
                """
                SELECT * FROM system_events
                WHERE category = ?
                ORDER BY id DESC LIMIT ?
                """,
                (category, limit),
            )
        else:
            cursor = self.conn.execute(
                """
                SELECT * FROM system_events
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            )
        return [dict(row) for row in cursor.fetchall()]
