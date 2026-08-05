"""Tests for the Trend Discovery pipeline (Phase 4)."""

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Dict
import pytest

from hermes_social.services.brand import BrandSystem
from hermes_social.trends.dedup import deduplicate_candidates
from hermes_social.trends.freshness import compute_freshness, filter_stale
from hermes_social.trends.gap_analyzer import analyze_content_gap
from hermes_social.trends.models import RawCandidate, ScoredCandidate
from hermes_social.trends.normalizer import normalize_candidates
from hermes_social.trends.pipeline import run_discovery_cycle
from hermes_social.trends.scorer import score_candidates


@pytest.fixture
def sample_candidates() -> list[RawCandidate]:
    now = datetime.now(timezone.utc)
    return [
        RawCandidate(
            title="Building an Agentic AI System with Python",
            url="https://example.com/agentic-ai",
            source_type="hackernews",
            source_name="Hacker News",
            published_at=now - timedelta(hours=2),
            discovered_at=now,
            excerpt="<p>A deep dive into building agents.</p>",
            tags=[],
            engagement_signals={"points": 250},
            raw_url="https://example.com/agentic-ai?utm_source=hn"
        ),
        RawCandidate(
            title="The state of frontend web development in 2024",
            url="https://example.com/frontend",
            source_type="devto",
            source_name="Dev.to",
            published_at=now - timedelta(hours=48),
            discovered_at=now,
            excerpt="React, Vue, and the rest...",
            tags=["webdev", "frontend"],
            engagement_signals={"reactions": 150},
            raw_url="https://example.com/frontend"
        ),
        RawCandidate(
            title="Very old news about machine learning",
            url="https://example.com/old",
            source_type="rss",
            source_name="OldFeed",
            published_at=now - timedelta(days=5),
            discovered_at=now,
            excerpt="This is old.",
            tags=[],
            engagement_signals={},
            raw_url="https://example.com/old"
        )
    ]


def test_normalize_strips_html_and_params(sample_candidates):
    normalized = normalize_candidates(sample_candidates)
    
    assert "<p>" not in normalized[0].excerpt
    assert normalized[0].excerpt == "A deep dive into building agents."
    assert "utm_source" not in normalized[0].url


def test_dedup_exact_url_match(sample_candidates):
    # Add a duplicate with the same URL
    dup = RawCandidate(**sample_candidates[0].__dict__)
    candidates = sample_candidates + [dup]
    
    deduped = deduplicate_candidates(candidates, [])
    assert len(deduped) == len(sample_candidates)


def test_dedup_title_similarity(sample_candidates):
    # Add a fuzzy duplicate title
    dup = RawCandidate(**sample_candidates[0].__dict__)
    dup.title = "Building an Agentic AI System with Python (2024)"
    dup.url = "https://example.com/different-url"
    candidates = sample_candidates + [dup]
    
    deduped = deduplicate_candidates(candidates, [])
    assert len(deduped) == len(sample_candidates)


def test_freshness_score_new_item():
    now = datetime.now(timezone.utc)
    score = compute_freshness(now - timedelta(hours=1))
    assert score > 90.0


def test_freshness_score_old_item():
    now = datetime.now(timezone.utc)
    score = compute_freshness(now - timedelta(hours=80), max_age_hours=72)
    assert score == 0.0


def test_filter_stale_removes_old(sample_candidates):
    fresh = filter_stale(sample_candidates, max_age_hours=72)
    assert len(fresh) == 2  # The 5-day old one is removed


def test_score_candidate_with_pillar_match(sample_candidates, brand_system: BrandSystem, sources_config: Dict):
    fresh = filter_stale(sample_candidates)
    scored = score_candidates(fresh, brand_system, sources_config["scoring_weights"], [], sources_config)
    
    # "agentic AI" should match pillar and have a high score
    assert scored[0].matched_pillar == "AI & Agentic Systems"
    assert scored[0].opportunity_score > 50.0


def test_gap_analysis_no_existing(sample_candidates, brand_system: BrandSystem, sources_config: Dict):
    fresh = filter_stale(sample_candidates)
    scored = score_candidates(fresh, brand_system, sources_config["scoring_weights"], [], sources_config)
    
    notes = analyze_content_gap(scored[0], [], [])
    assert any("Opportunity" in n for n in notes)


def test_discovery_pipeline_dry_run(db_conn: sqlite3.Connection, brand_system: BrandSystem, sources_config: Dict):
    """Test full pipeline runs without error in dry_run mode."""
    # This will hit actual APIs since we didn't mock them, but it shouldn't write to DB
    result = run_discovery_cycle(
        conn=db_conn,
        brand=brand_system,
        sources_config=sources_config,
        min_opportunity_score=10.0,  # low threshold to ensure some pass
        dry_run=True
    )
    
    assert result.total_fetched >= 0
    
    # DB should still be empty
    cursor = db_conn.execute("SELECT count(*) FROM topics")
    assert cursor.fetchone()[0] == 0
