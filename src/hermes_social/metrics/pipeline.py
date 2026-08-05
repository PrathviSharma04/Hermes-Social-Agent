"""Snapshot pipeline for metrics collection."""

import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from hermes_social.config import AppConfig
from hermes_social.constants import PostStatus, PerformanceWindow, Platform
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.db.repositories.performance import PerformanceRepository
from hermes_social.metrics.registry import get_collector

logger = logging.getLogger(__name__)


def calculate_due_windows(published_at: datetime, now: datetime) -> List[PerformanceWindow]:
    """Calculate which performance windows have elapsed since publish time."""
    delta = now - published_at
    windows = []
    
    if delta >= timedelta(hours=2):
        windows.append(PerformanceWindow.HOUR_2)
    if delta >= timedelta(hours=24):
        windows.append(PerformanceWindow.HOUR_24)
    if delta >= timedelta(hours=72):
        windows.append(PerformanceWindow.HOUR_72)
    if delta >= timedelta(days=7):
        windows.append(PerformanceWindow.DAY_7)
        
    return windows


def run_metrics_collection(config: AppConfig, conn: sqlite3.Connection) -> None:
    """
    Main entry point for the metrics pipeline.
    Finds PUBLISHED posts and checks if any new snapshot windows have been crossed.
    """
    logger.info("Starting Metrics Collection pipeline...")
    
    post_repo = PostRepository(conn)
    perf_repo = PerformanceRepository(conn)
    
    # We only care about posts published recently (e.g., within the last 10 days)
    # This avoids querying 7d metrics on posts from 3 years ago
    fourteen_days_ago = datetime.now() - timedelta(days=14)
    
    # Custom query because we need to filter by date
    cursor = conn.execute(
        """
        SELECT id, platform, status, scheduled_at, updated_at 
        FROM posts 
        WHERE status = ? 
        AND updated_at > ?
        """, 
        (PostStatus.PUBLISHED.value, fourteen_days_ago.strftime('%Y-%m-%d %H:%M:%S'))
    )
    published_posts = [dict(row) for row in cursor.fetchall()]
    
    if not published_posts:
        logger.info("No recent published posts to check for metrics.")
        return
        
    now = datetime.now()
    collected_count = 0
    
    for post in published_posts:
        # Use scheduled_at as a proxy for published_at (since there is no dedicated column)
        # If scheduled_at is missing, use updated_at (which is when status became PUBLISHED)
        pub_str = post.get("scheduled_at") or post.get("updated_at")
        if not pub_str:
            continue
            
        try:
            published_at = datetime.strptime(pub_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            logger.warning(f"Could not parse date for post {post['id']}: {pub_str}")
            continue
            
        due_windows = calculate_due_windows(published_at, now)
        
        # Check which snapshots we already have
        existing_snapshots = perf_repo.list_by_post(post["id"])
        existing_windows = {snap["window"] for snap in existing_snapshots}
        
        for window in due_windows:
            if window.value not in existing_windows:
                logger.info(f"Triggering {window.value} snapshot for Post {post['id']}")
                
                try:
                    platform = Platform(post["platform"])
                    collector = get_collector(platform, config)
                    
                    # Assume platform_post_id would normally be fetched from a join with publishing result
                    # For MVP, we use post_id as a string placeholder
                    platform_post_id = f"mock_pid_{post['id']}"
                    
                    metrics = collector.fetch_metrics(platform_post_id, window)
                    
                    perf_repo.upsert_snapshot(post["id"], window, metrics)
                    conn.commit()
                    collected_count += 1
                except Exception as e:
                    logger.error(f"Failed to collect metrics for Post {post['id']}: {e}")
                    
    logger.info(f"Metrics collection complete. Collected {collected_count} new snapshots.")
