"""Tests for Content Generation pipeline (Phase 6)."""

import sqlite3
from unittest.mock import patch, MagicMock

import pytest

from hermes_social.constants import TopicStatus, PostStatus
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.db.repositories.research import ResearchRepository
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.generation.adapters import adapt_for_instagram, adapt_for_linkedin, adapt_for_x
from hermes_social.generation.council import run_content_council
from hermes_social.generation.editor import evaluate_drafts
from hermes_social.generation.models import MasterNarrative, PlatformDraft, CriticFeedback
from hermes_social.generation.narrative import generate_master_narrative
from hermes_social.generation.pipeline import generate_content_for_topic
from hermes_social.generation.safety import run_safety_checks
from hermes_social.research.models import KnowledgePack


@pytest.fixture
def dummy_knowledge_pack():
    return KnowledgePack(
        topic="Agentic AI",
        why_now="High Trend Velocity",
        audience_relevance="AI Builders",
        verified_facts=["Agents are cool"],
        important_numbers=["10x faster"],
        context="Context",
        what_people_get_wrong=["Not just chatbots"],
        opposing_views=["Too expensive"],
        uncertainties=["When AGI?"],
        potential_angles=["Builders perspective"],
        source_map=[],
        claims=[],
        overall_confidence=95.0,
        research_run_id=1
    )


def test_master_narrative_mocked(db_conn, dummy_knowledge_pack):
    brand_context = {"brand_voice": "Bold", "content_pillars": ["AI"]}
    
    # We use the built-in mock response route
    narrative = generate_master_narrative(db_conn, dummy_knowledge_pack, brand_context, model_route="mock")
    
    assert narrative.hook == "Mock Hook"
    assert narrative.core_thesis == "Mock Thesis"
    assert len(narrative.evidence) > 0


def test_platform_adapters_mocked(db_conn):
    brand_context = {}
    narrative = MasterNarrative(
        hook="H", core_thesis="T", why_it_matters="W", evidence=[], insight="I", practical_takeaway="P", optional_cta=None
    )
    
    draft_li = adapt_for_linkedin(db_conn, narrative, brand_context, model_route="mock")
    assert draft_li.platform == "linkedin"
    
    draft_x = adapt_for_x(db_conn, narrative, brand_context, model_route="mock")
    assert draft_x.platform == "x"


def test_content_council_mocked(db_conn, dummy_knowledge_pack):
    drafts = [
        PlatformDraft(platform="linkedin", text_content="content", format_type="text")
    ]
    
    council_fb = run_content_council(db_conn, drafts, dummy_knowledge_pack, model_route="mock")
    assert "Research Critic" in council_fb
    assert council_fb["Research Critic"].score == 90
    assert council_fb["Brand Critic"].score == 95


def test_editor_in_chief_mocked(db_conn):
    council_fb = {
        "Human-Writing Critic": CriticFeedback(score=90, critique="Good", critical_flags=[]),
        "Brand Critic": CriticFeedback(score=95, critique="Great", critical_flags=[]),
        "Research Critic": CriticFeedback(score=92, critique="Solid", critical_flags=[])
    }
    
    decision = evaluate_drafts(db_conn, council_fb, model_route="mock")
    
    # Since scores are high and no flags, the mock's "PASS" stands
    assert decision.decision == "PASS"


def test_editor_in_chief_hard_gates_fail(db_conn):
    council_fb = {
        "Human-Writing Critic": CriticFeedback(score=80, critique="Too AI sounding", critical_flags=[]), # < 85
        "Brand Critic": CriticFeedback(score=95, critique="Great", critical_flags=[]),
        "Research Critic": CriticFeedback(score=92, critique="Solid", critical_flags=[])
    }
    
    # Even if mock returns "PASS", the hard gate overrides it to "REVISE"
    decision = evaluate_drafts(db_conn, council_fb, model_route="mock")
    assert decision.decision == "REVISE"
    assert "AUTOMATED GATE" in decision.revision_notes


def test_safety_checks():
    draft = PlatformDraft(platform="x", text_content="This is amazing software.", format_type="text")
    
    # Duplicate pass
    assert run_safety_checks(draft, past_posts=["Different post"], banned_phrases=["buy now"]) == True
    
    # Duplicate fail
    assert run_safety_checks(draft, past_posts=["this is amazing software."], banned_phrases=[]) == False
    
    # Banned phrase fail
    assert run_safety_checks(draft, past_posts=[], banned_phrases=["amazing software"]) == False
    
    # Fake experience fail
    draft_anecdote = PlatformDraft(platform="x", text_content="When I was working there...", format_type="text")
    assert run_safety_checks(draft_anecdote, past_posts=[], banned_phrases=[]) == False


def test_generation_pipeline_success(db_conn: sqlite3.Connection):
    topic_repo = TopicRepository(db_conn)
    research_repo = ResearchRepository(db_conn)
    post_repo = PostRepository(db_conn)
    
    topic_id = topic_repo.create({
        "canonical_topic": "AI Trends",
        "status": TopicStatus.RESEARCHED.value
    })
    
    run_id = research_repo.create_run(topic_id, "mock")
    research_repo.complete_run(run_id, 95.0, "Done")
    
    success, msgs = generate_content_for_topic(db_conn, topic_id, {}, model_route="mock")
    
    assert success is True, msgs
    
    # Verify DB state
    topic = topic_repo.get_by_id(topic_id)
    assert topic["status"] == TopicStatus.WRITTEN.value
    
    # Verify posts were created
    posts = post_repo.get_recent_posts(30)
    assert len(posts) == 3 # LI, X, IG
    for p in posts:
        assert p["status"] == PostStatus.DRAFT.value
