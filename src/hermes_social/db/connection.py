"""SQLite database connection manager and transaction context for Hermes Social Agent."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

from hermes_social.db.migrations import apply_migrations


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create and configure an SQLite database connection.

    Enforces WAL mode, busy timeout, foreign keys, and dictionary-like row factory.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row

    # Execute pragmas
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")

    return conn


def init_db(db_path: Path, migrations_dir: Optional[Path] = None) -> List[int]:
    """Initialize SQLite database and execute pending schema migrations."""
    with get_connection(db_path) as conn:
        applied = apply_migrations(conn, migrations_dir)
    return applied


@contextmanager
def db_session(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection context manager.

    Commits on successful block completion, rolls back on exception, and closes connection.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
