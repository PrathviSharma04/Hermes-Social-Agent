"""Syncs SQLite database state to the Obsidian vault."""

import logging
import sqlite3
import datetime
import re
from pathlib import Path

from hermes_social.obsidian.models import VaultSyncResult, DecisionEntry
from hermes_social.obsidian.writers import (
    render_strategy_rules_page,
    render_experiment_page,
    render_monthly_review,
    render_decision_log_entry,
)
from hermes_social.db.repositories.strategy import StrategyRepository
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.constants import Platform

logger = logging.getLogger(__name__)


def _atomic_write(file_path: Path, content: str) -> None:
    """Writes content to a temporary file then renames it for atomicity."""
    tmp_path = file_path.with_suffix('.tmp')
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    tmp_path.replace(file_path)


def sync_strategy_rules(conn: sqlite3.Connection, vault_path: Path) -> int:
    """Syncs strategy rules to 02-Strategy-Rules/{platform}.md"""
    repo = StrategyRepository(conn)
    files_written = 0
    target_dir = vault_path / "02-Strategy-Rules"
    
    for platform in Platform:
        rules = repo.list_rules(platform=platform.value)
        content = render_strategy_rules_page(platform.value, rules)
        
        file_path = target_dir / f"{platform.value}.md"
        _atomic_write(file_path, content)
        files_written += 1
        
    return files_written


def sync_experiments(conn: sqlite3.Connection, vault_path: Path) -> int:
    """Syncs non-DRAFT experiments to 03-Experiments/"""
    repo = ExperimentRepository(conn)
    cursor = conn.execute("SELECT * FROM experiments WHERE status != 'DRAFT'")
    experiments = [dict(row) for row in cursor.fetchall()]
    
    files_written = 0
    target_dir = vault_path / "03-Experiments"
    
    for exp in experiments:
        exp_id = exp["id"]
        slug = re.sub(r'[^a-z0-9]+', '-', exp["name"].lower()).strip('-')
        
        # Get assignments
        cursor = conn.execute("SELECT * FROM post_experiment_assignments WHERE experiment_id = ?", (exp_id,))
        assignments = [dict(row) for row in cursor.fetchall()]
        
        content = render_experiment_page(exp, assignments)
        file_path = target_dir / f"experiment-{exp_id}-{slug}.md"
        _atomic_write(file_path, content)
        files_written += 1
        
    return files_written


def generate_monthly_review(conn: sqlite3.Connection, vault_path: Path, year: int, month: int) -> int:
    """Generates a monthly review based on aggregated stats."""
    start_date = f"{year}-{month:02d}-01 00:00:00"
    if month == 12:
        end_date = f"{year+1}-01-01 00:00:00"
    else:
        end_date = f"{year}-{month+1:02d}-01 00:00:00"
        
    stats = {
        "total_published": 0,
        "platform_breakdown": {},
        "topics_discovered": 0,
        "topics_accepted": 0,
        "topics_rejected": 0,
        "experiments_completed": 0,
        "rules_confirmed": 0
    }
    
    # Aggregate data using SQL
    # Published posts
    cursor = conn.execute(
        "SELECT platform, COUNT(*) FROM posts WHERE status = 'PUBLISHED' AND published_at >= ? AND published_at < ? GROUP BY platform",
        (start_date, end_date)
    )
    for row in cursor.fetchall():
        platform, count = row
        stats["platform_breakdown"][platform] = count
        stats["total_published"] += count
        
    # Topics
    cursor = conn.execute(
        "SELECT status, COUNT(*) FROM topics WHERE created_at >= ? AND created_at < ? GROUP BY status",
        (start_date, end_date)
    )
    for row in cursor.fetchall():
        status, count = row
        if status == 'DISCOVERED':
            stats["topics_discovered"] += count
        elif status == 'ACCEPTED':
            stats["topics_accepted"] += count
        elif status == 'REJECTED':
            stats["topics_rejected"] += count
            
    # Experiments
    cursor = conn.execute(
        "SELECT COUNT(*) FROM experiments WHERE status = 'COMPLETED' AND updated_at >= ? AND updated_at < ?",
        (start_date, end_date)
    )
    stats["experiments_completed"] = cursor.fetchone()[0]
    
    # Rules confirmed
    cursor = conn.execute(
        "SELECT COUNT(*) FROM strategy_rules WHERE status = 'CONFIRMED' AND last_validated_at >= ? AND last_validated_at < ?",
        (start_date, end_date)
    )
    stats["rules_confirmed"] = cursor.fetchone()[0]
    
    content = render_monthly_review(year, month, stats)
    file_path = vault_path / "00-Dashboard" / f"Monthly-Review-{year}-{month:02d}.md"
    _atomic_write(file_path, content)
    
    return 1


def append_decision(vault_path: Path, decision: DecisionEntry) -> int:
    """Appends an entry to the decision log."""
    file_path = vault_path / "04-Decision-Log" / "decisions.md"
    content = render_decision_log_entry(decision)
    
    # Ensure file exists with a header if it's new
    if not file_path.exists():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Decision Log\n\nThis log tracks manual user overrides and strategy adjustments.\n\n")
            
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(content)
        
    return 1


def sync_vault(conn: sqlite3.Connection, vault_path: Path) -> VaultSyncResult:
    """
    Main entry point to sync the SQLite database state into the Obsidian vault.
    """
    logger.info("Starting SQLite -> Obsidian Vault sync...")
    result = VaultSyncResult()
    
    try:
        # Sync strategy rules
        rules_written = sync_strategy_rules(conn, vault_path)
        result.files_written += rules_written
        
        # Sync experiments
        exp_written = sync_experiments(conn, vault_path)
        result.files_written += exp_written
        
        # Generate current monthly review automatically
        now = datetime.datetime.utcnow()
        rev_written = generate_monthly_review(conn, vault_path, now.year, now.month)
        result.files_written += rev_written
        
        result.sync_timestamp = now.isoformat()
        logger.info(f"Vault sync complete. {result.files_written} files written.")
        
    except Exception as e:
        logger.error(f"Error during vault sync: {e}")
        result.errors.append(str(e))
        
    return result
