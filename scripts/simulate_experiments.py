"""
Simulation script for Phase 13 Exit Gate.
Proves the experiment engine can successfully evaluate statistical significance
and promote a winner to a strategy rule.
"""

import sqlite3
import random
from pathlib import Path

from hermes_social.config import AppConfig
from hermes_social.db.connection import get_connection
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.experiments.engine import start_experiment, assign_post, evaluate_experiment


def run_simulation():
    print("=" * 60)
    print("Hermes Social Agent — Experiment Simulation (Phase 13)")
    print("=" * 60)
    
    # We will use an in-memory database with the full schema
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    
    # 1. Initialize Schema
    schema_path = Path("migrations/001_initial_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
        
    print("[*] Initialized in-memory SQLite schema.")
    conn.execute("PRAGMA foreign_keys = OFF;")
    
    # 2. Create a Mock Experiment
    repo = ExperimentRepository(conn)
    exp_id = repo.create({
        "name": "Hook Length Test",
        "hypothesis": "Short hooks get more impressions.",
        "platform": "linkedin",
        "variable": "hook_length",
        "variant_a": "Short (<8 words)",
        "variant_b": "Long (>15 words)",
        "minimum_samples": 10
    })
    print(f"[*] Created mock experiment (ID={exp_id}): Hook Length Test (A: Short, B: Long)")
    
    # 3. Start Experiment
    success = start_experiment(exp_id, conn)
    assert success, "Failed to start experiment"
    print("[*] Experiment set to ACTIVE.")
    
    # 4. Generate Baseline
    # We need a historical baseline in performance_snapshots for linkedin_carousel
    # Let's say median impressions for linkedin_carousel is 1000
    conn.execute(
        "INSERT INTO content_ideas (id, topic_id, angle, status) VALUES (1, 1, 'mock', 'mock')"
    )
    conn.execute(
        "INSERT INTO posts (id, content_idea_id, platform, format, body, status, idempotency_key) VALUES (999, 1, 'linkedin', 'carousel', 'mock body', 'PUBLISHED', 'mock_key_999')"
    )
    conn.execute(
        "INSERT INTO performance_snapshots (post_id, window, impressions, likes) VALUES (999, '24h', 1000, 100)"
    )
    
    # 5. Generate Posts and Assign Variants
    print("[*] Generating 25 mock posts and assigning variants...")
    for i in range(1, 26):
        # Insert a mock post
        conn.execute(
            "INSERT INTO posts (id, content_idea_id, platform, format, body, status, idempotency_key) VALUES (?, 1, 'linkedin', 'carousel', 'mock body', 'PUBLISHED', ?)",
            (i, f"mock_key_{i}")
        )
        
        # Assign it
        variant = assign_post(i, "linkedin", conn)
        
        # Generate performance snapshot
        # Variant A (Short) performs well: 1.5x to 2.5x the median (1500 - 2500 impressions)
        # Variant B (Long) performs poorly: 0.5x to 1.0x the median (500 - 1000 impressions)
        if variant == "A":
            impressions = random.randint(1500, 2500)
        else:
            impressions = random.randint(500, 1000)
            
        conn.execute(
            "INSERT INTO performance_snapshots (post_id, window, impressions) VALUES (?, '24h', ?)",
            (i, impressions)
        )
        
    # Check assignments
    cursor = conn.execute("SELECT variant, COUNT(*) FROM post_experiment_assignments GROUP BY variant")
    for row in cursor.fetchall():
        print(f"  - Assigned Variant {row[0]}: {row[1]} posts")
        
    # 6. Evaluate Experiment
    print("[*] Evaluating experiment with scipy.stats...")
    evaluate_experiment(exp_id, conn)
    
    # 7. Check Results
    exp = repo.get_by_id(exp_id)
    print("\n--- Evaluation Results ---")
    print(f"Status:     {exp['status']}")
    print(f"Conclusion: {exp['conclusion']}")
    
    assert exp["status"] == "COMPLETED", "Experiment did not complete"
    
    # 8. Check Strategy Promotion
    cursor = conn.execute("SELECT * FROM strategy_rules")
    rules = [dict(r) for r in cursor.fetchall()]
    print("\n--- Strategy Rules ---")
    if not rules:
        print("No rules promoted.")
    for r in rules:
        print(f"Rule: {r['rule']}")
        print(f"Evidence: {r['evidence_summary']}")
        print(f"Confidence: {r['confidence']:.2%}")
        print(f"Status: {r['status']}")
        
    assert len(rules) == 1, "Strategy rule was not generated"
    assert rules[0]["status"] == "CONFIRMED"
    
    print("\n[+] Exit Gate passed successfully.")
    
if __name__ == "__main__":
    run_simulation()
