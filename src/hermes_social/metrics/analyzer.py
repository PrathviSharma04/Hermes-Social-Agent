"""Performance baselining and normalization logic (Phase 12)."""

import logging
import sqlite3
import statistics
from typing import Dict, Any, Tuple, Optional

from hermes_social.constants import PerformanceWindow

logger = logging.getLogger(__name__)


def calculate_median_baselines(conn: sqlite3.Connection) -> Dict[str, Dict[str, float]]:
    """
    Calculate the historical median performance (impressions, likes) 
    grouped by platform and post format at the 24h window.
    
    Returns:
        { "platform_format": {"impressions": 1000.0, "likes": 50.0} }
    """
    cursor = conn.execute(
        """
        SELECT p.platform, p.format, s.impressions, s.likes
        FROM posts p
        JOIN performance_snapshots s ON p.id = s.post_id
        WHERE s.window = ? AND s.impressions IS NOT NULL
        """,
        (PerformanceWindow.HOUR_24.value,)
    )
    
    rows = cursor.fetchall()
    groups: Dict[str, Dict[str, list]] = {}
    
    for row in rows:
        platform = row["platform"]
        fmt = row["format"] or "unknown"
        key = f"{platform}_{fmt}"
        
        if key not in groups:
            groups[key] = {"impressions": [], "likes": []}
            
        if row["impressions"] is not None:
            groups[key]["impressions"].append(row["impressions"])
        if row["likes"] is not None:
            groups[key]["likes"].append(row["likes"])
            
    baselines = {}
    for key, metrics in groups.items():
        imp = metrics["impressions"]
        lik = metrics["likes"]
        
        baselines[key] = {
            "impressions": statistics.median(imp) if imp else 0.0,
            "likes": statistics.median(lik) if lik else 0.0
        }
        
    return baselines


def evaluate_post(post_id: int, conn: sqlite3.Connection) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Compare a post's 24h metrics against its specific platform/format baseline.
    Returns (post_metrics_dict, baseline_score_string)
    """
    cursor = conn.execute(
        """
        SELECT p.platform, p.format, s.impressions, s.likes
        FROM posts p
        LEFT JOIN performance_snapshots s ON p.id = s.post_id AND s.window = ?
        WHERE p.id = ?
        """,
        (PerformanceWindow.HOUR_24.value, post_id)
    )
    row = cursor.fetchone()
    
    if not row:
        return {}, "Post not found"
        
    if row["impressions"] is None:
        return {"platform": row["platform"], "format": row["format"]}, "Waiting for 24h snapshot"
        
    baselines = calculate_median_baselines(conn)
    key = f"{row['platform']}_{row['format'] or 'unknown'}"
    baseline = baselines.get(key)
    
    if not baseline or baseline["impressions"] == 0:
        score_str = "No historical baseline yet"
    else:
        multiplier = row["impressions"] / baseline["impressions"]
        score_str = f"{multiplier:.1f}x median impressions"
        
    post_metrics = {
        "platform": row["platform"],
        "format": row["format"],
        "impressions": row["impressions"],
        "likes": row["likes"]
    }
    
    return post_metrics, score_str
