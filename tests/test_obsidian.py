"""Tests for Obsidian Vault System (Phase 9)."""

import sqlite3
from pathlib import Path
from hermes_social.obsidian.vault_init import initialize_vault, VAULT_FOLDERS
from hermes_social.obsidian.models import DecisionEntry
from hermes_social.obsidian.writers import (
    render_strategy_rules_page,
    render_experiment_page,
    render_monthly_review,
    render_decision_log_entry,
)
from hermes_social.obsidian.sync import (
    sync_strategy_rules,
    sync_experiments,
    generate_monthly_review,
    append_decision,
    sync_vault
)

def test_initialize_vault(tmp_path: Path):
    vault_path = tmp_path / "test_vault"
    initialize_vault(vault_path)
    
    # Check folders
    for folder in VAULT_FOLDERS:
        assert (vault_path / folder).is_dir()
        
    # Check README
    readme = vault_path / "README.md"
    assert readme.is_file()
    assert "Hermes Social Agent Vault" in readme.read_text(encoding="utf-8")
    
    # Check idempotency
    initialize_vault(vault_path)
    assert readme.is_file()

def test_render_strategy_rules_page():
    rules = [
        {"id": 1, "rule": "Use emojis", "status": "CONFIRMED", "confidence": 90.5, "sample_size": 10},
        {"id": 2, "rule": "Post at 9am", "status": "TESTING", "confidence": 40.0, "sample_size": 2}
    ]
    content = render_strategy_rules_page("linkedin", rules)
    
    assert "platform: linkedin" in content
    assert "## ✅ CONFIRMED" in content
    assert "### Rule 1: Use emojis" in content
    assert "## 🧪 TESTING" in content

def test_render_experiment_page():
    exp = {
        "id": 1, "name": "Image vs Text", "status": "ACTIVE", "variable": "format",
        "hypothesis": "Images perform better."
    }
    assignments = [{"post_id": 10, "variant": "A"}]
    content = render_experiment_page(exp, assignments)
    
    assert "experiment_id: 1" in content
    assert "status: ACTIVE" in content
    assert "# 🧪 Image vs Text" in content
    assert "Post ID 10 (Variant A)" in content

def test_render_monthly_review():
    stats = {
        "total_published": 10,
        "platform_breakdown": {"linkedin": 6, "x": 4},
        "topics_discovered": 5,
        "experiments_completed": 1
    }
    content = render_monthly_review(2026, 8, stats)
    
    assert "month: 2026-08" in content
    assert "Total Posts Published**: 10" in content
    assert "Linkedin: 6" in content

def test_append_decision(tmp_path: Path):
    vault_path = tmp_path / "vault"
    (vault_path / "04-Decision-Log").mkdir(parents=True)
    
    decision = DecisionEntry(
        timestamp="2026-08-05T12:00:00",
        category="Strategy Override",
        description="Changed publish time.",
        old_value="09:00",
        new_value="10:00",
        reason="Better engagement."
    )
    
    append_decision(vault_path, decision)
    
    log_file = vault_path / "04-Decision-Log" / "decisions.md"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "# Decision Log" in content
    assert "Changed publish time." in content
