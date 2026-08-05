#!/usr/bin/env python3
"""Script to initialize SQLite database and execute pending schema migrations."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hermes_social.config import load_config
from hermes_social.db.connection import get_connection, init_db
from hermes_social.db.migrations import get_current_version


def main() -> int:
    """Initialize database and print schema status summary."""
    print("Initializing Hermes Social Agent Database...")
    config = load_config()
    db_path = config.database_path

    applied_versions = init_db(db_path)
    with get_connection(db_path) as conn:
        current_ver = get_current_version(conn)
        cursor = conn.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        table_count = int(cursor.fetchone()[0])

    print("=============================================")
    print(f"Database Path:      {db_path}")
    print(f"Migrations Applied: {len(applied_versions)} {applied_versions}")
    print(f"Schema Version:     {current_ver}")
    print(f"Table Count:        {table_count}")
    print("=============================================")
    print("Status: Database initialized successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
