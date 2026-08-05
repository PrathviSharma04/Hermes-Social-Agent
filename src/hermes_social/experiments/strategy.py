"""Strategy Promotion logic."""

import sqlite3
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def promote_to_strategy(exp_id: int, winning_variant: str, confidence: float, conn: sqlite3.Connection) -> None:
    """
    Promotes a completed and won experiment into a CONFIRMED strategy rule.
    """
    cursor = conn.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
    row = cursor.fetchone()
    if not row:
        logger.error(f"Cannot promote experiment {exp_id}: Not found.")
        return
        
    exp = dict(row)
    platform = exp.get("platform")
    variable = exp["variable"]
    
    # We'll construct a readable rule string
    variant_val = exp["variant_a"] if winning_variant == "A" else exp["variant_b"]
    
    rule_str = f"Prefer '{variant_val}' for variable '{variable}'"
    
    # Calculate total sample size
    sample_size_cursor = conn.execute(
        "SELECT COUNT(*) FROM post_experiment_assignments WHERE experiment_id = ?",
        (exp_id,)
    )
    total_samples = sample_size_cursor.fetchone()[0]
    
    conclusion = exp.get("conclusion", "Experiment concluded.")
    
    # Insert into strategy_rules
    conn.execute(
        """
        INSERT INTO strategy_rules (
            platform, rule, evidence_summary, sample_size, confidence, status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (platform, rule_str, conclusion, total_samples, confidence, "CONFIRMED")
    )
    conn.commit()
    
    logger.info(f"Promoted experiment {exp_id} to CONFIRMED strategy rule on {platform}.")
