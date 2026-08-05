"""Tests for the Research + Fact Checking pipeline (Phase 5)."""

import sqlite3
from pathlib import Path
import pytest

from hermes_social.constants import ClaimType, TopicStatus, VerificationStatus
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.research.claim_extractor import extract_claims
from hermes_social.research.claim_mapper import map_claims_to_sources
from hermes_social.research.confidence import compute_research_confidence
from hermes_social.research.contradiction_detector import detect_contradictions
from hermes_social.research.knowledge_pack import build_knowledge_pack
from hermes_social.research.pipeline import run_research_for_topic
from hermes_social.research.vault_writer import write_knowledge_pack_to_vault


def test_extract_claims(mock_fetched_sources):
    claims = extract_claims(mock_fetched_sources)
    assert len(claims) > 0
    
    # "50% faster" should be extracted as numerical
    num_claims = [c for c in claims if c.is_numerical]
    assert len(num_claims) >= 2
    
    # "I think" -> OPINION
    op_claims = [c for c in claims if c.claim_type == ClaimType.OPINION.value]
    assert len(op_claims) >= 1
    
    # "expected to" / "will" -> PREDICTION
    pred_claims = [c for c in claims if c.claim_type == ClaimType.PREDICTION.value]
    assert len(pred_claims) >= 1


def test_map_claims_to_sources(mock_fetched_sources):
    raw_claims = extract_claims(mock_fetched_sources)
    mapped = map_claims_to_sources(raw_claims, mock_fetched_sources)
    
    # The 50% faster claim should be in both source 1 and 2, boosting confidence
    multi_source = [c for c in mapped if len(c.source_urls) > 1]
    assert len(multi_source) >= 1
    assert multi_source[0].confidence > 60.0
    assert multi_source[0].verification_status == VerificationStatus.VERIFIED.value


def test_detect_contradictions(mock_fetched_sources):
    raw_claims = extract_claims(mock_fetched_sources)
    analyzed = detect_contradictions(raw_claims)
    
    # "will change the world" vs "will not change the world" should flag contradiction
    disputed = [c for c in analyzed if c.verification_status == VerificationStatus.DISPUTED.value]
    assert len(disputed) >= 2
    assert "negation" in disputed[0].contradiction_notes.lower()


def test_compute_confidence(mock_fetched_sources):
    raw_claims = extract_claims(mock_fetched_sources)
    mapped = map_claims_to_sources(raw_claims, mock_fetched_sources)
    analyzed = detect_contradictions(mapped)
    
    confidence = compute_research_confidence(analyzed, mock_fetched_sources)
    # It should be reduced by the contradiction penalty, but boosted by authority and multi-source
    assert 0.0 <= confidence <= 100.0


def test_knowledge_pack_vault_output(tmp_path: Path, mock_fetched_sources):
    raw_claims = extract_claims(mock_fetched_sources)
    mapped = map_claims_to_sources(raw_claims, mock_fetched_sources)
    analyzed = detect_contradictions(mapped)
    confidence = compute_research_confidence(analyzed, mock_fetched_sources)
    
    topic = {"canonical_topic": "AI Performance Metrics"}
    pack = build_knowledge_pack(topic, mock_fetched_sources, analyzed, 999, confidence)
    
    vault_path = tmp_path
    filepath = write_knowledge_pack_to_vault(pack, vault_path)
    
    assert filepath.exists()
    content = filepath.read_text(encoding="utf-8")
    assert "AI Performance Metrics" in content
    assert "VERIFIED FACTS" in content
    assert "WHAT PEOPLE ARE GETTING WRONG" in content
    assert "Overall Confidence:" in content


def test_research_pipeline_dry_run(db_conn: sqlite3.Connection, tmp_path: Path):
    """Test full pipeline runs without error in dry_run mode."""
    # Seed a topic
    repo = TopicRepository(db_conn)
    topic_id = repo.create({
        "canonical_topic": "Test Research Topic",
        "status": TopicStatus.ACCEPTED.value
    })
    repo.add_source(topic_id, {
        "source_type": "hackernews",
        "source_name": "Hacker News",
        "url": "https://example.com/mock-hn-story",
        "authority_score": 90.0
    })
    
    # This will fetch example.com which just returns dummy HTML, but the pipeline handles it
    result = run_research_for_topic(db_conn, topic_id, tmp_path, dry_run=True)
    
    assert result.topic_id == topic_id
    assert result.knowledge_pack is not None
    
    # DB shouldn't be modified
    cursor = db_conn.execute("SELECT count(*) FROM research_runs")
    assert cursor.fetchone()[0] == 0


def test_no_fabricated_sources(mock_fetched_sources):
    """Exit Gate Check: No claim can be generated without being linked to a fetched source."""
    raw_claims = extract_claims(mock_fetched_sources)
    mapped = map_claims_to_sources(raw_claims, mock_fetched_sources)
    
    for claim in mapped:
        if claim.confidence > 0:
            assert len(claim.source_urls) > 0, "Claim with confidence must have at least one source URL"
            assert len(claim.source_ids) > 0, "Claim must have DB source IDs"
