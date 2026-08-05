"""Core engine for A/B testing variables and managing experiment lifecycles."""

import logging
import random
import sqlite3
from typing import Optional, Dict, Any, Tuple
import numpy as np
from scipy import stats

from hermes_social.constants import ExperimentStatus
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.metrics.analyzer import evaluate_post
from hermes_social.experiments.strategy import promote_to_strategy

logger = logging.getLogger(__name__)


def start_experiment(exp_id: int, conn: sqlite3.Connection) -> bool:
    """
    Start an experiment if no overlapping experiment is active on the same platform.
    """
    repo = ExperimentRepository(conn)
    exp = repo.get_by_id(exp_id)
    
    if not exp:
        logger.error(f"Experiment {exp_id} not found.")
        return False
        
    if exp["status"] != ExperimentStatus.DRAFT.value:
        logger.error(f"Experiment {exp_id} is not in DRAFT status.")
        return False
        
    platform = exp.get("platform")
    
    # Check for active experiments on the same platform
    active_exps = repo.list_active(platform=platform)
    if active_exps:
        logger.warning(f"Cannot start experiment {exp_id}: Platform {platform} already has active experiments.")
        return False
        
    repo.update_status(exp_id, ExperimentStatus.ACTIVE)
    conn.commit()
    logger.info(f"Experiment {exp_id} started successfully.")
    return True


def assign_post(post_id: int, platform: str, conn: sqlite3.Connection) -> Optional[str]:
    """
    Finds an active experiment for the post's platform and assigns it to Variant A or B.
    """
    repo = ExperimentRepository(conn)
    active_exps = repo.list_active(platform=platform)
    
    if not active_exps:
        return None
        
    # Just take the first active one for this platform
    exp = active_exps[0]
    exp_id = exp["id"]
    
    # Check if already assigned
    existing = repo.get_assignment(post_id, exp_id)
    if existing:
        return existing["variant"]
        
    # Count current assignments to balance them
    cursor = conn.execute(
        "SELECT variant, COUNT(*) FROM post_experiment_assignments WHERE experiment_id = ? GROUP BY variant",
        (exp_id,)
    )
    counts = dict(cursor.fetchall())
    count_a = counts.get("A", 0)
    count_b = counts.get("B", 0)
    
    # Simple balancing: if one has less, pick it. Else random.
    if count_a < count_b:
        variant = "A"
    elif count_b < count_a:
        variant = "B"
    else:
        variant = random.choice(["A", "B"])
        
    repo.assign_post(post_id, exp_id, variant)
    conn.commit()
    logger.info(f"Assigned post {post_id} to Variant {variant} for experiment {exp_id}.")
    return variant


def evaluate_experiment(exp_id: int, conn: sqlite3.Connection) -> None:
    """
    Evaluates an experiment if sample sizes are met. Calculates p-value and confidence.
    """
    repo = ExperimentRepository(conn)
    exp = repo.get_by_id(exp_id)
    
    if not exp or exp["status"] != ExperimentStatus.ACTIVE.value:
        return
        
    min_samples = exp.get("minimum_samples", 10)
    
    # Get assignments
    cursor = conn.execute(
        """
        SELECT post_id, variant 
        FROM post_experiment_assignments 
        WHERE experiment_id = ?
        """, (exp_id,)
    )
    assignments = cursor.fetchall()
    
    # Group posts by variant
    a_posts = [row["post_id"] for row in assignments if row["variant"] == "A"]
    b_posts = [row["post_id"] for row in assignments if row["variant"] == "B"]
    
    # Collect 24h baseline scores for each group
    # A score is a float multiplier, e.g., 1.5 for 1.5x median impressions
    a_scores = []
    b_scores = []
    
    for pid in a_posts:
        metrics, score_str = evaluate_post(pid, conn)
        if metrics and "impressions" in metrics:
            try:
                # Extract the float multiplier from "1.5x median impressions"
                if "x" in score_str:
                    mult = float(score_str.split("x")[0])
                    a_scores.append(mult)
            except ValueError:
                pass
            
    for pid in b_posts:
        metrics, score_str = evaluate_post(pid, conn)
        if metrics and "impressions" in metrics:
            try:
                if "x" in score_str:
                    mult = float(score_str.split("x")[0])
                    b_scores.append(mult)
            except ValueError:
                pass
            
    if len(a_scores) < min_samples or len(b_scores) < min_samples:
        logger.info(f"Experiment {exp_id} still collecting samples. A: {len(a_scores)}/{min_samples}, B: {len(b_scores)}/{min_samples}")
        return
        
    # We have enough samples! Time to evaluate using scipy stats.
    # Mann-Whitney U test is good for non-parametric multipliers
    statistic, p_value = stats.mannwhitneyu(a_scores, b_scores, alternative='two-sided')
    
    median_a = np.median(a_scores)
    median_b = np.median(b_scores)
    
    # Confidence level is roughly 1 - p_value
    confidence = 1.0 - p_value
    
    # Check if statistically significant (e.g., p < 0.05)
    winner = None
    if p_value < 0.05:
        if median_a > median_b:
            winner = "A"
            conclusion = f"Variant A won (p={p_value:.4f}, confidence={confidence:.2%}). Median A: {median_a:.2f}x, Median B: {median_b:.2f}x."
        else:
            winner = "B"
            conclusion = f"Variant B won (p={p_value:.4f}, confidence={confidence:.2%}). Median B: {median_b:.2f}x, Median A: {median_a:.2f}x."
    else:
        conclusion = f"No significant difference (p={p_value:.4f}). Median A: {median_a:.2f}x, Median B: {median_b:.2f}x."
        
    # Update experiment
    conn.execute(
        """
        UPDATE experiments 
        SET status = ?, confidence = ?, conclusion = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (ExperimentStatus.COMPLETED.value, float(confidence), conclusion, exp_id)
    )
    
    # Check if this was a revalidation
    if exp["variable"].startswith("retest_rule_"):
        try:
            rule_id = int(exp["variable"].replace("retest_rule_", ""))
            if winner == "A":
                # Rule still works! Restore confidence.
                logger.info(f"Revalidation of Rule {rule_id} succeeded. Restoring confidence.")
                conn.execute(
                    "UPDATE strategy_rules SET status = 'CONFIRMED', confidence = 0.95, last_validated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (rule_id,)
                )
            else:
                # Rule no longer works. Retire it.
                logger.info(f"Revalidation of Rule {rule_id} failed. Retiring rule.")
                conn.execute(
                    "UPDATE strategy_rules SET status = 'RETIRED' WHERE id = ?",
                    (rule_id,)
                )
        except ValueError:
            pass
    elif winner:
        # Standard promotion
        promote_to_strategy(exp_id, winner, confidence, conn)
        
    conn.commit()
    logger.info(f"Experiment {exp_id} COMPLETED. {conclusion}")
