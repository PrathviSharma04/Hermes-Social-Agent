"""SQLite online backup, restore, and retention management for Hermes Social Agent."""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def backup_database(
    db_path: Path, backup_dir: Path, retention_days: int = 30
) -> Path:
    """Create a timestamped online SQLite database backup and prune old backups.

    Returns the path to the newly created backup file.
    """
    db_path = Path(db_path)
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"hermes_social_{timestamp}.db"

    # Use SQLite online backup API
    src_conn = sqlite3.connect(str(db_path))
    dst_conn = sqlite3.connect(str(backup_file))
    try:
        with dst_conn:
            src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    # Retention cleanup
    if retention_days > 0:
        cutoff_seconds = time.time() - (retention_days * 86400)
        for old_backup in backup_dir.glob("hermes_social_*.db"):
            try:
                if old_backup.stat().st_mtime < cutoff_seconds:
                    old_backup.unlink()
            except OSError:
                pass

    return backup_file


def restore_database(backup_path: Path, target_path: Path) -> None:
    """Restore a SQLite database from a backup file after verifying integrity."""
    backup_path = Path(backup_path)
    target_path = Path(target_path)

    if not backup_path.exists() or not backup_path.is_file():
        raise ValueError(f"Backup file does not exist: {backup_path}")

    # Verify backup integrity
    try:
        chk_conn = sqlite3.connect(str(backup_path))
        cursor = chk_conn.execute("PRAGMA integrity_check")
        row = cursor.fetchone()
        chk_conn.close()
        if not row or row[0].lower() != "ok":
            raise ValueError("Backup integrity check failed.")
    except Exception as exc:
        raise ValueError(f"Invalid or corrupt SQLite backup file: {exc}") from exc

    target_path.parent.mkdir(parents=True, exist_ok=True)
    src_conn = sqlite3.connect(str(backup_path))
    dst_conn = sqlite3.connect(str(target_path))
    try:
        with dst_conn:
            src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()


def list_backups(backup_dir: Path) -> List[Dict[str, Any]]:
    """List available backups in backup_dir sorted newest first."""
    backup_dir = Path(backup_dir)
    if not backup_dir.exists() or not backup_dir.is_dir():
        return []

    backups: List[Dict[str, Any]] = []
    for fpath in backup_dir.glob("hermes_social_*.db"):
        stat = fpath.stat()
        backups.append(
            {
                "filename": fpath.name,
                "path": str(fpath.resolve()),
                "size_bytes": stat.st_size,
                "created_at": datetime.fromtimestamp(
                    stat.st_mtime, timezone.utc
                ).isoformat(),
            }
        )

    backups.sort(key=lambda x: str(x["created_at"]), reverse=True)
    return backups
