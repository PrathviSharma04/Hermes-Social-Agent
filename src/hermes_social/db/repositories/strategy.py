"""Strategy and brand rules database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union

from hermes_social.constants import StrategyRuleStatus
from hermes_social.core.state_machine import validate_strategy_rule_transition


class StrategyRepository:
    """Repository for managing learned strategy rules and brand rules in SQLite."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_rule(self, rule_data: Dict[str, Any]) -> int:
        """Create a new strategy rule (starts as HYPOTHESIS by default)."""
        cursor = self.conn.execute(
            """
            INSERT INTO strategy_rules (
                platform, rule, evidence_summary, sample_size,
                confidence, status
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rule_data["platform"],
                rule_data["rule"],
                rule_data.get("evidence_summary"),
                rule_data.get("sample_size", 0),
                rule_data.get("confidence", 0.0),
                rule_data.get("status", StrategyRuleStatus.HYPOTHESIS.value),
            ),
        )
        return int(cursor.lastrowid)

    def get_rule_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a strategy rule by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM strategy_rules WHERE id = ?", (rule_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_rule_status(
        self,
        rule_id: int,
        new_status: Union[StrategyRuleStatus, str],
        sample_size: Optional[int] = None,
        min_samples_for_confirmed: int = 10,
    ) -> None:
        """Update strategy rule status, enforcing minimum sample size for CONFIRMED status."""
        rule = self.get_rule_by_id(rule_id)
        if not rule:
            raise ValueError(f"Strategy Rule {rule_id} not found.")

        current_status = rule["status"]
        validate_strategy_rule_transition(current_status, new_status)

        target_status = (
            new_status.value
            if isinstance(new_status, StrategyRuleStatus)
            else str(new_status)
        )
        current_samples = (
            sample_size if sample_size is not None else int(rule["sample_size"])
        )

        if (
            target_status == StrategyRuleStatus.CONFIRMED.value
            and current_samples < min_samples_for_confirmed
        ):
            raise ValueError(
                f"Cannot promote rule to CONFIRMED without sufficient sample size (required: >= {min_samples_for_confirmed}, found: {current_samples})."
            )

        if sample_size is not None:
            self.conn.execute(
                """
                UPDATE strategy_rules
                SET status = ?, sample_size = ?, last_validated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_status, sample_size, rule_id),
            )
        else:
            self.conn.execute(
                """
                UPDATE strategy_rules
                SET status = ?, last_validated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (target_status, rule_id),
            )

    def list_rules(
        self,
        platform: Optional[str] = None,
        status: Optional[Union[StrategyRuleStatus, str]] = None,
    ) -> List[Dict[str, Any]]:
        """List strategy rules filtered by platform and/or status."""
        query = "SELECT * FROM strategy_rules WHERE 1=1"
        params: List[Any] = []

        if platform:
            query += " AND platform = ?"
            params.append(platform)
        if status:
            status_val = (
                status.value if isinstance(status, StrategyRuleStatus) else str(status)
            )
            query += " AND status = ?"
            params.append(status_val)

        query += " ORDER BY id DESC"
        cursor = self.conn.execute(query, tuple(params))
        return [dict(row) for row in cursor.fetchall()]

    def create_brand_rule(
        self, rule_name: str, rule_text: str, is_active: bool = True
    ) -> int:
        """Create a new brand rule."""
        cursor = self.conn.execute(
            """
            INSERT INTO brand_rules (rule_name, rule_text, is_active)
            VALUES (?, ?, ?)
            """,
            (rule_name, rule_text, 1 if is_active else 0),
        )
        return int(cursor.lastrowid)

    def list_active_brand_rules(self) -> List[Dict[str, Any]]:
        """Retrieve all currently active brand rules."""
        cursor = self.conn.execute(
            "SELECT * FROM brand_rules WHERE is_active = 1 ORDER BY id ASC"
        )
        return [dict(row) for row in cursor.fetchall()]
