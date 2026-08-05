"""Research runs and claims database repository."""

import sqlite3
from typing import Any, Dict, List, Optional, Union
from hermes_social.constants import ClaimType, ResearchStatus, VerificationStatus


class ResearchRepository:
    """Repository for managing research runs, claims, and claim-source mappings."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_run(self, topic_id: int, model_route: str) -> int:
        """Start a new research run for a topic."""
        cursor = self.conn.execute(
            """
            INSERT INTO research_runs (topic_id, model_route, status)
            VALUES (?, ?, ?)
            """,
            (topic_id, model_route, ResearchStatus.RUNNING.value),
        )
        return int(cursor.lastrowid)

    def get_run_by_id(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a research run by ID."""
        cursor = self.conn.execute(
            "SELECT * FROM research_runs WHERE id = ?", (run_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def complete_run(self, run_id: int, confidence: float, summary: str) -> None:
        """Mark a research run as successfully completed."""
        self.conn.execute(
            """
            UPDATE research_runs
            SET status = ?, completed_at = CURRENT_TIMESTAMP,
                confidence = ?, research_summary = ?
            WHERE id = ?
            """,
            (ResearchStatus.COMPLETED.value, confidence, summary, run_id),
        )

    def fail_run(self, run_id: int, error: str) -> None:
        """Mark a research run as failed."""
        self.conn.execute(
            """
            UPDATE research_runs
            SET status = ?, completed_at = CURRENT_TIMESTAMP,
                research_summary = ?
            WHERE id = ?
            """,
            (ResearchStatus.FAILED.value, f"FAILED: {error}", run_id),
        )

    def add_claim(self, run_id: int, claim_data: Dict[str, Any]) -> int:
        """Add a factual claim discovered during research."""
        claim_type = claim_data.get("claim_type", ClaimType.FACT.value)
        verification_status = claim_data.get(
            "verification_status", VerificationStatus.UNVERIFIED.value
        )
        cursor = self.conn.execute(
            """
            INSERT INTO research_claims (
                research_run_id, claim, claim_type, confidence,
                verification_status, contradiction_status, source_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                claim_data["claim"],
                claim_type,
                claim_data.get("confidence", 0.0),
                verification_status,
                claim_data.get("contradiction_status"),
                claim_data.get("source_count", 0),
            ),
        )
        return int(cursor.lastrowid)

    def link_claim_source(self, claim_id: int, source_id: int) -> None:
        """Link a research claim to a discovered topic source."""
        self.conn.execute(
            """
            INSERT OR IGNORE INTO claim_sources (claim_id, source_id)
            VALUES (?, ?)
            """,
            (claim_id, source_id),
        )
        # Increment source count on claim
        self.conn.execute(
            """
            UPDATE research_claims
            SET source_count = (
                SELECT COUNT(*) FROM claim_sources WHERE claim_id = ?
            )
            WHERE id = ?
            """,
            (claim_id, claim_id),
        )

    def get_claims_by_run(self, run_id: int) -> List[Dict[str, Any]]:
        """Retrieve all claims associated with a research run."""
        cursor = self.conn.execute(
            "SELECT * FROM research_claims WHERE research_run_id = ? ORDER BY id ASC",
            (run_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_latest_run_id(self, topic_id: int) -> Optional[int]:
        """Retrieve the latest completed research run ID for a topic."""
        cursor = self.conn.execute(
            "SELECT id FROM research_runs WHERE topic_id = ? AND status = ? ORDER BY id DESC LIMIT 1",
            (topic_id, ResearchStatus.COMPLETED.value)
        )
        row = cursor.fetchone()
        return row[0] if row else None
