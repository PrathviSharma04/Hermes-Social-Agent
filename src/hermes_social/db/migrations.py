"""Lightweight SQLite schema migration runner."""

import re
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple


def get_default_migrations_dir() -> Path:
    """Return the default path to the migrations directory."""
    # Project root is 4 levels up from this module (src/hermes_social/db/migrations.py -> project root)
    return Path(__file__).resolve().parent.parent.parent.parent / "migrations"


def create_migrations_table(conn: sqlite3.Connection) -> None:
    """Ensure the schema_migrations tracking table exists."""
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def get_current_version(conn: sqlite3.Connection) -> int:
    """Return the highest applied migration version number, or 0 if none applied."""
    create_migrations_table(conn)
    cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
    row = cursor.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return 0


def get_pending_migrations(
    conn: sqlite3.Connection, migrations_dir: Optional[Path] = None
) -> List[Tuple[int, Path]]:
    """Scan migrations directory and return sorted list of unapplied (version, path) tuples."""
    if migrations_dir is None:
        migrations_dir = get_default_migrations_dir()

    if not migrations_dir.exists() or not migrations_dir.is_dir():
        return []

    current_version = get_current_version(conn)
    pending: List[Tuple[int, Path]] = []

    pattern = re.compile(r"^(\d{3,})_.*\.sql$")
    for file_path in migrations_dir.glob("*.sql"):
        match = pattern.match(file_path.name)
        if match:
            version = int(match.group(1))
            if version > current_version:
                pending.append((version, file_path))

    pending.sort(key=lambda x: x[0])
    return pending


def apply_migrations(
    conn: sqlite3.Connection, migrations_dir: Optional[Path] = None
) -> List[int]:
    """Apply all pending SQL migrations in order inside a transaction.

    Returns list of applied migration versions.
    """
    if migrations_dir is None:
        migrations_dir = get_default_migrations_dir()

    create_migrations_table(conn)
    pending = get_pending_migrations(conn, migrations_dir)
    applied_versions: List[int] = []

    for version, file_path in pending:
        sql_script = file_path.read_text(encoding="utf-8")
        with conn:
            conn.executescript(sql_script)
            conn.execute(
                "INSERT INTO schema_migrations (version, filename) VALUES (?, ?)",
                (version, file_path.name),
            )
        applied_versions.append(version)

    return applied_versions
