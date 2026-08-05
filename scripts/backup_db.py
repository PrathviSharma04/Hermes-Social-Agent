#!/usr/bin/env python3
"""Script to backup the Hermes Social Agent SQLite database."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from hermes_social.config import load_config
from hermes_social.db.backup import backup_database


def main() -> int:
    """Create a database backup and print result."""
    config = load_config()
    db_path = config.database_path
    backup_dir = db_path.parent / "backups"

    if not db_path.exists():
        print(f"Error: Database {db_path} does not exist. Run init_db first.")
        return 1

    print(f"Backing up database from {db_path}...")
    backup_path = backup_database(db_path, backup_dir)
    stat = backup_path.stat()
    print("=============================================")
    print(f"Backup File:  {backup_path.name}")
    print(f"Backup Path:  {backup_path}")
    print(f"Size (bytes): {stat.st_size}")
    print("=============================================")
    print("Status: Database backup completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
