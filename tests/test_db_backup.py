"""Tests for SQLite online backup, restore, and integrity verification."""

import sqlite3
from pathlib import Path
import pytest
from hermes_social.db.backup import (
    backup_database,
    list_backups,
    restore_database,
)
from hermes_social.db.connection import get_connection, init_db
from hermes_social.db.repositories.topics import TopicRepository


def test_backup_and_restore_cycle(tmp_path: Path) -> None:
    """Test online backup creation, listing, and restore with integrity verification."""
    db_path = tmp_path / "hermes_original.db"
    backup_dir = tmp_path / "backups"
    restore_path = tmp_path / "hermes_restored.db"

    # Initialize DB and insert a topic
    init_db(db_path)
    with get_connection(db_path) as conn:
        repo = TopicRepository(conn)
        topic_id = repo.create(
            {"canonical_topic": "Backup Test Topic", "opportunity_score": 95.0}
        )
        conn.commit()

    # Create backup
    backup_path = backup_database(db_path, backup_dir, retention_days=30)
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0

    # Test list_backups
    backups = list_backups(backup_dir)
    assert len(backups) == 1
    assert backups[0]["filename"] == backup_path.name

    # Restore to a new location and verify content
    restore_database(backup_path, restore_path)
    assert restore_path.exists()

    with get_connection(restore_path) as conn:
        repo = TopicRepository(conn)
        topic = repo.get_by_id(topic_id)
        assert topic is not None
        assert topic["canonical_topic"] == "Backup Test Topic"


def test_restore_corrupt_file_raises_error(tmp_path: Path) -> None:
    """Test that attempting to restore a corrupt file fails integrity check and raises ValueError."""
    corrupt_file = tmp_path / "corrupt.db"
    target_file = tmp_path / "target.db"
    corrupt_file.write_text("This is not an SQLite database file.", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid or corrupt SQLite backup file"):
        restore_database(corrupt_file, target_file)
