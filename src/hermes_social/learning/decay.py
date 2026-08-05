"""Confidence Decay and Stale-Rule Revalidation."""

import logging
import sqlite3
from datetime import datetime
from hermes_social.db.repositories.experiments import ExperimentRepository

logger = logging.getLogger(__name__)


def decay_confidence(conn: sqlite3.Connection) -> None:
    """
    Decays confidence of CONFIRMED strategy rules over time.
    If confidence drops < 0.70, spawns a revalidation experiment and marks rule as TESTING.
    If confidence drops < 0.30, retires the rule.
    """
    # SQLite datetime('now') and julian day math to get days passed
    cursor = conn.execute(
        """
        SELECT id, platform, rule, evidence_summary, sample_size, confidence, status,
               last_validated_at,
               (julianday('now') - julianday(last_validated_at)) AS days_passed
        FROM strategy_rules
        WHERE status = 'CONFIRMED'
        """
    )
    rules = cursor.fetchall()
    
    for row in rules:
        rule_id = row["id"]
        days_passed = row["days_passed"] or 0
        current_confidence = row["confidence"]
        
        # Decay rate: 2% per week (7 days)
        # Total decay = (days_passed / 7) * 0.02
        decay = (days_passed / 7.0) * 0.02
        new_confidence = current_confidence - decay
        
        if new_confidence > current_confidence:
            new_confidence = current_confidence  # should not happen but just in case
            
        logger.info(f"Rule {rule_id}: Confidence decayed from {current_confidence:.2f} to {new_confidence:.2f}")
        
        if new_confidence < 0.30:
            logger.info(f"Rule {rule_id} dropped below 0.30 confidence. RETIRING.")
            conn.execute("UPDATE strategy_rules SET status = 'RETIRED', confidence = ? WHERE id = ?", (new_confidence, rule_id))
        elif new_confidence < 0.70:
            logger.info(f"Rule {rule_id} dropped below 0.70 confidence. Triggering Revalidation.")
            conn.execute("UPDATE strategy_rules SET status = 'TESTING', confidence = ? WHERE id = ?", (new_confidence, rule_id))
            
            # Spawn revalidation experiment
            repo = ExperimentRepository(conn)
            # We attempt to parse the rule text or just set up a generic re-test
            repo.create({
                "name": f"Re-validation of Rule {rule_id}",
                "hypothesis": f"Re-testing: {row['rule']}",
                "platform": row["platform"],
                "variable": f"retest_rule_{rule_id}",
                "variant_a": "Adhere to Rule",
                "variant_b": "Control (Ignore Rule)",
                "minimum_samples": 10
            })
        else:
            # Just update the confidence meter
            conn.execute("UPDATE strategy_rules SET confidence = ? WHERE id = ?", (new_confidence, rule_id))
            
    conn.commit()
