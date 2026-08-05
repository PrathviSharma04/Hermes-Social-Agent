"""Tests for Phase 14 Self-Learning Engine."""

import sqlite3
import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from hermes_social.config import AppConfig
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.learning.observer import generate_observations
from hermes_social.learning.hypothesizer import generate_hypotheses, HypothesesList, GeneratedHypothesis
from hermes_social.learning.decay import decay_confidence


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # minimal schema
    conn.executescript("""
        CREATE TABLE experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            platform TEXT,
            variable TEXT NOT NULL,
            variant_a TEXT NOT NULL,
            variant_b TEXT NOT NULL,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            minimum_samples INTEGER DEFAULT 10,
            status TEXT NOT NULL DEFAULT 'DRAFT',
            confidence REAL DEFAULT 0.0,
            conclusion TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE strategy_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            rule TEXT NOT NULL,
            evidence_summary TEXT,
            sample_size INTEGER DEFAULT 0,
            confidence REAL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'HYPOTHESIS',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            format TEXT,
            hook TEXT,
            word_count INTEGER,
            slide_count INTEGER,
            body TEXT,
            status TEXT NOT NULL,
            published_at TIMESTAMP,
            scheduled_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE post_experiment_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            experiment_id INTEGER NOT NULL,
            variant TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    yield conn
    conn.close()


@patch("hermes_social.learning.observer.evaluate_post")
def test_generate_observations(mock_evaluate, db_conn):
    # Insert posts
    now = datetime.utcnow()
    db_conn.execute("INSERT INTO posts (id, platform, format, status, updated_at) VALUES (1, 'linkedin', 'text', 'PUBLISHED', ?)", (now,))
    db_conn.execute("INSERT INTO posts (id, platform, format, status, updated_at) VALUES (2, 'linkedin', 'text', 'PUBLISHED', ?)", (now,))
    db_conn.execute("INSERT INTO posts (id, platform, format, status, updated_at) VALUES (3, 'linkedin', 'text', 'PUBLISHED', ?)", (now,))
    
    # Assign post 3 to an experiment so it is excluded
    db_conn.execute("INSERT INTO post_experiment_assignments (post_id, experiment_id, variant) VALUES (3, 1, 'A')")
    
    # Mock evaluates
    def side_effect(post_id, conn):
        if post_id == 1:
            return {"impressions": 2000}, "2.0x median impressions"  # HIGH OUTLIER
        elif post_id == 2:
            return {"impressions": 1000}, "1.0x median impressions"  # NORMAL
            
    mock_evaluate.side_effect = side_effect
    
    obs = generate_observations(db_conn)
    
    # Post 3 should be excluded (experiment). Post 2 should be excluded (not an outlier).
    assert len(obs) == 1
    assert obs[0]["post_id"] == 1
    assert obs[0]["performance"] == "HIGH OUTLIER"


@patch("hermes_social.learning.hypothesizer.execute_prompt")
def test_exit_gate_no_instant_rule_promotion(mock_execute, db_conn):
    """
    EXIT GATE TEST: The agent cannot promote a rule based on one post.
    Generating a hypothesis should ONLY write to `experiments` with minimum_samples > 1,
    and MUST NOT write to `strategy_rules`.
    """
    mock_execute.return_value = {
        "hypotheses": [
            {
                "name": "Test Hook Length",
                "hypothesis": "Short hooks are better",
                "platform": "linkedin",
                "variable": "hook_length",
                "variant_a": "Short",
                "variant_b": "Long"
            }
        ]
    }
    
    config = AppConfig(database_path=":memory:")
    
    obs = [{"post_id": 1, "performance": "HIGH OUTLIER", "platform": "linkedin", "variable": "hook_length"}]
    
    generate_hypotheses(db_conn, config, obs)
    
    # Verify it was added to experiments
    repo = ExperimentRepository(db_conn)
    exps = db_conn.execute("SELECT * FROM experiments").fetchall()
    assert len(exps) == 1
    
    exp = dict(exps[0])
    assert exp["status"] == "DRAFT"
    assert exp["minimum_samples"] >= 10, "Exit Gate Failed: minimum_samples is not enforcing multiple posts."
    
    # Verify nothing was added to strategy_rules
    rules = db_conn.execute("SELECT * FROM strategy_rules").fetchall()
    assert len(rules) == 0, "Exit Gate Failed: Agent promoted a rule immediately."


def test_decay_confidence_and_revalidation(db_conn):
    # Insert a confirmed rule from 14 days ago (2 weeks)
    # Decay should be 2 weeks * 0.02 = 0.04
    past_date = (datetime.utcnow() - timedelta(days=14)).isoformat()
    db_conn.execute(
        """
        INSERT INTO strategy_rules (id, platform, rule, confidence, status, last_validated_at) 
        VALUES (1, 'linkedin', 'Test Rule', 0.95, 'CONFIRMED', ?)
        """, (past_date,)
    )
    
    # Insert a confirmed rule from 100 days ago (14+ weeks)
    # Decay should be ~14.2 * 0.02 = 0.28. 0.95 - 0.28 = 0.67 (< 0.70)
    stale_date = (datetime.utcnow() - timedelta(days=100)).isoformat()
    db_conn.execute(
        """
        INSERT INTO strategy_rules (id, platform, rule, confidence, status, last_validated_at) 
        VALUES (2, 'linkedin', 'Stale Rule', 0.95, 'CONFIRMED', ?)
        """, (stale_date,)
    )
    
    decay_confidence(db_conn)
    
    # Check Rule 1 (decayed, but still CONFIRMED)
    r1 = dict(db_conn.execute("SELECT * FROM strategy_rules WHERE id = 1").fetchone())
    assert r1["status"] == "CONFIRMED"
    assert 0.90 < r1["confidence"] < 0.92
    
    # Check Rule 2 (decayed below 0.70, should be TESTING)
    r2 = dict(db_conn.execute("SELECT * FROM strategy_rules WHERE id = 2").fetchone())
    assert r2["status"] == "TESTING"
    assert r2["confidence"] < 0.70
    
    # Check if a revalidation experiment was spawned for Rule 2
    exps = [dict(r) for r in db_conn.execute("SELECT * FROM experiments").fetchall()]
    assert len(exps) == 1
    assert exps[0]["variable"] == "retest_rule_2"
    assert "Re-validation" in exps[0]["name"]
