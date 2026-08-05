"""Tests for the Experiment Engine."""

import sqlite3
import pytest
from datetime import datetime
from unittest.mock import patch

from hermes_social.constants import ExperimentStatus
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.experiments.engine import start_experiment, assign_post, evaluate_experiment


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
        CREATE TABLE post_experiment_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            experiment_id INTEGER NOT NULL,
            variant TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            status TEXT NOT NULL
        );
        CREATE TABLE performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            window TEXT NOT NULL,
            impressions INTEGER,
            likes INTEGER
        );
    """)
    yield conn
    conn.close()


def test_start_experiment_prevents_overlap(db_conn):
    repo = ExperimentRepository(db_conn)
    exp1 = repo.create({
        "name": "Exp 1",
        "hypothesis": "H1",
        "platform": "linkedin",
        "variable": "v1",
        "variant_a": "A",
        "variant_b": "B"
    })
    exp2 = repo.create({
        "name": "Exp 2",
        "hypothesis": "H2",
        "platform": "linkedin",
        "variable": "v2",
        "variant_a": "A",
        "variant_b": "B"
    })
    
    assert start_experiment(exp1, db_conn) == True
    # Cannot start exp2 because exp1 is active on linkedin
    assert start_experiment(exp2, db_conn) == False


def test_assign_post_balances_variants(db_conn):
    repo = ExperimentRepository(db_conn)
    exp1 = repo.create({
        "name": "Exp 1",
        "hypothesis": "H1",
        "platform": "x",
        "variable": "v1",
        "variant_a": "A",
        "variant_b": "B"
    })
    start_experiment(exp1, db_conn)
    
    # Assign post 1
    v1 = assign_post(1, "x", db_conn)
    assert v1 in ["A", "B"]
    
    # Assign post 2
    v2 = assign_post(2, "x", db_conn)
    # The engine should balance them, so v2 should be the opposite of v1
    assert set([v1, v2]) == {"A", "B"}


@patch("hermes_social.experiments.engine.evaluate_post")
def test_evaluate_experiment(mock_evaluate_post, db_conn):
    repo = ExperimentRepository(db_conn)
    exp1 = repo.create({
        "name": "Exp 1",
        "hypothesis": "H1",
        "platform": "linkedin",
        "variable": "v1",
        "variant_a": "A",
        "variant_b": "B",
        "minimum_samples": 3 # small for test
    })
    start_experiment(exp1, db_conn)
    
    # Assign 6 posts
    assign_post(1, "linkedin", db_conn)
    assign_post(2, "linkedin", db_conn)
    assign_post(3, "linkedin", db_conn)
    assign_post(4, "linkedin", db_conn)
    assign_post(5, "linkedin", db_conn)
    assign_post(6, "linkedin", db_conn)
    
    # Let's say all odds are A and evens are B for mocking (or whatever engine did)
    # Actually engine balances them perfectly so 1,3,5 are one and 2,4,6 are another.
    
    # Mock evaluate_post to return a high score for variant A posts, low for B
    def side_effect(pid, conn):
        # We need to know which variant pid is
        cursor = conn.execute("SELECT variant FROM post_experiment_assignments WHERE post_id=?", (pid,))
        var = cursor.fetchone()["variant"]
        if var == "A":
            return {"impressions": 2000}, "2.0x median impressions"
        else:
            return {"impressions": 1000}, "1.0x median impressions"
            
    mock_evaluate_post.side_effect = side_effect
    
    evaluate_experiment(exp1, db_conn)
    
    exp = repo.get_by_id(exp1)
    assert exp["status"] == ExperimentStatus.COMPLETED.value
    assert "Variant A won" in exp["conclusion"]
    
    # Check strategy rule
    cursor = db_conn.execute("SELECT * FROM strategy_rules")
    rules = [dict(r) for r in cursor.fetchall()]
    assert len(rules) == 1
    assert rules[0]["platform"] == "linkedin"
    assert "Prefer 'A' for variable 'v1'" in rules[0]["rule"]
    assert rules[0]["status"] == "CONFIRMED"
