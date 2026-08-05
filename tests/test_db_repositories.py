"""Comprehensive tests for all SQLite domain repositories."""

import sqlite3
from datetime import datetime, timezone
import pytest
from hermes_social.constants import (
    ContentIdeaStatus,
    ExperimentStatus,
    PostFormat,
    PostStatus,
    QAStatus,
    StrategyRuleStatus,
    SystemEventLevel,
    TopicStatus,
)


def test_topic_repository_crud(topic_repo) -> None:
    """Test creating a topic, updating status, querying opportunities, and managing sources."""
    topic_id = topic_repo.create(
        {
            "canonical_topic": "AI Agents in Production",
            "summary": "Analysis of failure modes",
            "category": "AI/Dev",
            "opportunity_score": 88.5,
        }
    )
    assert topic_id > 0

    topic = topic_repo.get_by_id(topic_id)
    assert topic["canonical_topic"] == "AI Agents in Production"
    assert topic["status"] == TopicStatus.DISCOVERED.value

    # Test valid status transition
    topic_repo.update_status(topic_id, TopicStatus.EVALUATING)
    updated = topic_repo.get_by_id(topic_id)
    assert updated["status"] == TopicStatus.EVALUATING.value

    # Test top opportunities list
    opps = topic_repo.list_top_opportunities(limit=5)
    assert len(opps) == 1
    assert opps[0]["id"] == topic_id

    # Test adding source
    source_id = topic_repo.add_source(
        topic_id,
        {
            "source_type": "rss",
            "source_name": "Hacker News",
            "url": "https://news.ycombinator.com",
            "authority_score": 90.0,
        },
    )
    sources = topic_repo.get_sources(topic_id)
    assert len(sources) == 1
    assert sources[0]["id"] == source_id


def test_research_repository(topic_repo, research_repo) -> None:
    """Test creating research runs, claims, and linking claim provenance."""
    topic_id = topic_repo.create({"canonical_topic": "Test Topic"})
    source_id = topic_repo.add_source(
        topic_id, {"source_type": "web", "source_name": "Doc"}
    )

    run_id = research_repo.create_run(topic_id, "claude-opus-4-6")
    assert run_id > 0

    claim_id = research_repo.add_claim(
        run_id,
        {
            "claim": "Agents need idempotency keys in production.",
            "confidence": 0.95,
        },
    )
    assert claim_id > 0

    research_repo.link_claim_source(claim_id, source_id)
    claims = research_repo.get_claims_by_run(run_id)
    assert len(claims) == 1
    assert claims[0]["source_count"] == 1

    research_repo.complete_run(run_id, 0.92, "High confidence research complete.")
    run = research_repo.get_run_by_id(run_id)
    assert run["status"] == "COMPLETED"


def test_post_repository_idempotency_and_transitions(
    topic_repo, content_idea_repo, post_repo
) -> None:
    """Test post creation, mandatory idempotency key, uniqueness constraint, and transitions."""
    topic_id = topic_repo.create({"canonical_topic": "Test Topic"})
    idea_id = content_idea_repo.create(
        {"topic_id": topic_id, "angle": "Dev angle"}
    )

    # Missing idempotency_key must fail
    with pytest.raises(ValueError, match="idempotency_key is required"):
        post_repo.create(
            {
                "content_idea_id": idea_id,
                "platform": "linkedin",
                "format": PostFormat.CAROUSEL.value,
                "body": "Slide 1...",
            }
        )

    # Valid create
    post_id = post_repo.create(
        {
            "content_idea_id": idea_id,
            "platform": "linkedin",
            "format": PostFormat.CAROUSEL.value,
            "body": "Slide 1...",
            "idempotency_key": "unique-key-001",
        }
    )
    assert post_id > 0

    # Duplicate idempotency_key must raise SQLite IntegrityError
    with pytest.raises(sqlite3.IntegrityError):
        post_repo.create(
            {
                "content_idea_id": idea_id,
                "platform": "linkedin",
                "format": PostFormat.CAROUSEL.value,
                "body": "Slide 1 duplicate...",
                "idempotency_key": "unique-key-001",
            }
        )

    # Transition to READY_FOR_APPROVAL -> APPROVED -> SCHEDULED -> PUBLISHED
    post_repo.update_status(post_id, PostStatus.READY_FOR_APPROVAL)
    post_repo.update_status(post_id, PostStatus.APPROVED)
    post_repo.update_status(post_id, PostStatus.SCHEDULED)
    post_repo.mark_published(
        post_id, "linkedin_urn_123", "https://linkedin.com/feed/123"
    )

    post = post_repo.get_by_id(post_id)
    assert post["status"] == PostStatus.PUBLISHED.value
    assert post["platform_post_id"] == "linkedin_urn_123"


def test_performance_repository_nullable_metrics(
    topic_repo, content_idea_repo, post_repo, performance_repo
) -> None:
    """Test performance snapshot upserting and nullable metric handling (NULL not 0)."""
    topic_id = topic_repo.create({"canonical_topic": "Test Topic"})
    idea_id = content_idea_repo.create({"topic_id": topic_id, "angle": "Test"})
    post_id = post_repo.create(
        {
            "content_idea_id": idea_id,
            "platform": "x",
            "format": "TEXT",
            "body": "Hello X",
            "idempotency_key": "key-perf-1",
        }
    )

    # Upsert with some unavailable metrics (None)
    performance_repo.upsert_snapshot(
        post_id,
        "24h",
        {
            "impressions": 1500,
            "likes": 45,
            "saves": None,  # Unavailable on X, must store NULL not 0
            "shares": 12,
        },
    )

    snapshot = performance_repo.get_snapshot(post_id, "24h")
    assert snapshot["impressions"] == 1500
    assert snapshot["likes"] == 45
    assert snapshot["saves"] is None  # Verified NULL, not 0


def test_strategy_repository_minimum_sample_size(strategy_repo) -> None:
    """Test promoting rule to CONFIRMED enforces minimum sample size."""
    rule_id = strategy_repo.create_rule(
        {
            "platform": "linkedin",
            "rule": "5-8 word carousel hooks increase impressions",
            "sample_size": 4,
            "status": StrategyRuleStatus.HYPOTHESIS.value,
        }
    )

    strategy_repo.update_rule_status(rule_id, StrategyRuleStatus.TESTING)
    strategy_repo.update_rule_status(rule_id, StrategyRuleStatus.PROVISIONAL)

    # Promoting to CONFIRMED with sample_size < 10 must raise ValueError
    with pytest.raises(
        ValueError, match="Cannot promote rule to CONFIRMED without sufficient sample size"
    ):
        strategy_repo.update_rule_status(
            rule_id, StrategyRuleStatus.CONFIRMED, sample_size=4
        )

    # Updating with sample_size >= 10 succeeds
    strategy_repo.update_rule_status(
        rule_id, StrategyRuleStatus.CONFIRMED, sample_size=15
    )
    rule = strategy_repo.get_rule_by_id(rule_id)
    assert rule["status"] == StrategyRuleStatus.CONFIRMED.value
    assert rule["sample_size"] == 15


def test_operations_repository_audit_and_logging(operations_repo) -> None:
    """Test scheduled actions, Telegram audit logs, model run logs, and system events."""
    action_id = operations_repo.create_scheduled_action(
        {
            "action_type": "PUBLISH_POST",
            "payload_json": '{"post_id": 1}',
            "scheduled_for": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": "sched-key-1",
        }
    )
    assert action_id > 0

    cmd_id = operations_repo.log_telegram_command(
        "999999", "/status", "GET_STATUS", "PRINT_STATUS", "SUCCESS"
    )
    assert cmd_id > 0

    run_id = operations_repo.log_model_run(
        "TREND_EVALUATION", "claude-opus-4-6", success=True, quality_score=92.0
    )
    assert run_id > 0

    evt_id = operations_repo.log_system_event(
        SystemEventLevel.INFO, "DB", "Database schema initialized successfully"
    )
    events = operations_repo.list_system_events(limit=10)
    assert len(events) == 1
    assert events[0]["id"] == evt_id
