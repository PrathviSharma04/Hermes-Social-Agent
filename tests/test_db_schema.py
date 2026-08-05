"""Tests for SQLite database schema and migration runner."""

import sqlite3
import pytest
from hermes_social.db.connection import get_connection, init_db
from hermes_social.db.migrations import get_current_version


def test_all_schema_tables_created(db_conn: sqlite3.Connection) -> None:
    """Verify that all 17 normalized domain tables are created by migration 001."""
    expected_tables = {
        "topics",
        "topic_sources",
        "research_runs",
        "research_claims",
        "claim_sources",
        "content_ideas",
        "posts",
        "assets",
        "performance_snapshots",
        "experiments",
        "post_experiment_assignments",
        "strategy_rules",
        "brand_rules",
        "scheduled_actions",
        "telegram_commands",
        "model_runs",
        "system_events",
        "schema_migrations",
    }
    cursor = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    actual_tables = {row["name"] for row in cursor.fetchall()}
    assert expected_tables.issubset(actual_tables)


def test_migration_version_tracking(db_conn: sqlite3.Connection) -> None:
    """Verify schema_migrations tracks version 1 after init_db."""
    assert get_current_version(db_conn) == 1


def test_migration_idempotency(db_path) -> None:
    """Verify calling init_db multiple times does not error or reapply migrations."""
    applied_first = init_db(db_path)
    assert 1 in applied_first
    applied_second = init_db(db_path)
    assert applied_second == []


def test_foreign_key_enforcement(db_conn: sqlite3.Connection) -> None:
    """Verify that foreign keys are enabled and enforce reference constraints."""
    with pytest.raises(sqlite3.IntegrityError):
        db_conn.execute(
            """
            INSERT INTO topic_sources (topic_id, source_type, source_name)
            VALUES (99999, 'rss', 'Test Feed')
            """
        )
