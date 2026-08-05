"""Observation Generator: Scans past performance for anomalies."""

import logging
import sqlite3
from typing import List, Dict, Any

from hermes_social.metrics.analyzer import evaluate_post

logger = logging.getLogger(__name__)


def generate_observations(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Finds posts from the last 30 days that are outliers (either very good or very bad)
    and were not part of an experiment. Compiles them into a list of observations.
    """
    # Fetch posts not part of an experiment
    cursor = conn.execute(
        """
        SELECT p.id, p.platform, p.format, p.hook, p.word_count, p.slide_count, p.body,
               COALESCE(p.published_at, p.scheduled_at, p.updated_at) as pub_date
        FROM posts p
        LEFT JOIN post_experiment_assignments a ON p.id = a.post_id
        WHERE p.status = 'PUBLISHED'
          AND a.id IS NULL
          AND p.updated_at > datetime('now', '-30 days')
        ORDER BY p.id DESC
        """
    )
    posts = cursor.fetchall()
    
    observations = []
    
    for row in posts:
        post_id = row["id"]
        metrics, score_str = evaluate_post(post_id, conn)
        
        if not metrics or "impressions" not in metrics:
            continue
            
        multiplier = 1.0
        if "x" in score_str:
            try:
                multiplier = float(score_str.split("x")[0])
            except ValueError:
                pass
                
        # Define an outlier as > 1.5x median or < 0.5x median
        if multiplier >= 1.5:
            performance = "HIGH OUTLIER"
        elif multiplier <= 0.5:
            performance = "LOW OUTLIER"
        else:
            continue
            
        observations.append({
            "post_id": post_id,
            "platform": row["platform"],
            "format": row["format"],
            "hook": row["hook"],
            "word_count": row["word_count"],
            "slide_count": row["slide_count"],
            "body_snippet": row["body"][:100] + "..." if row["body"] else "",
            "multiplier": multiplier,
            "performance": performance
        })
        
    logger.info(f"Generated {len(observations)} raw observations.")
    return observations
