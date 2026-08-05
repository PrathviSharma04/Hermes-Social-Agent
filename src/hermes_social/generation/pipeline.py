"""Content Generation Pipeline."""

import logging
import sqlite3
from typing import List, Tuple

from hermes_social.constants import PostStatus, TopicStatus, Platform
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.db.repositories.research import ResearchRepository
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.generation.adapters import adapt_for_instagram, adapt_for_linkedin, adapt_for_x
from hermes_social.generation.council import run_content_council
from hermes_social.generation.editor import evaluate_drafts
from hermes_social.generation.narrative import generate_master_narrative
from hermes_social.generation.safety import run_safety_checks
from hermes_social.research.models import KnowledgePack, ExtractedClaim

logger = logging.getLogger(__name__)


def generate_content_for_topic(
    conn: sqlite3.Connection,
    topic_id: int,
    brand_context: dict,
    model_route: str = "gemini/gemini-1.5-pro",
    max_revisions: int = 3
) -> Tuple[bool, List[str]]:
    """Execute the full generation pipeline for a topic."""
    
    topic_repo = TopicRepository(conn)
    post_repo = PostRepository(conn)
    research_repo = ResearchRepository(conn)
    
    # 1. Update status
    topic_repo.update_status(topic_id, TopicStatus.WRITING.value)
    
    # 2. Reconstruct Knowledge Pack from DB
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        return False, ["Topic not found"]
        
    run_id = research_repo.get_latest_run_id(topic_id)
    if not run_id:
        return False, ["No research run found for topic"]
        
    db_claims = research_repo.get_claims_by_run(run_id)
    claims = [
        ExtractedClaim(
            claim_text=c["claim"],
            claim_type=c["claim_type"],
            source_urls=[],
            source_ids=[],
            confidence=c["confidence"],
            is_numerical=False,
            verification_status=c["verification_status"],
            contradiction_notes=c["contradiction_status"]
        )
        for c in db_claims
    ]
    
    pack = KnowledgePack(
        topic=topic["canonical_topic"],
        why_now="",
        audience_relevance="",
        verified_facts=[c.claim_text for c in claims if c.verification_status == "VERIFIED"],
        important_numbers=[],
        context="",
        what_people_get_wrong=[],
        opposing_views=[],
        uncertainties=[],
        potential_angles=[],
        source_map=[],
        claims=claims,
        overall_confidence=90.0,
        research_run_id=run_id
    )
    
    banned_phrases = brand_context.get("banned_phrases", [])
    past_posts = [p["body"] for p in post_repo.get_recent_posts(days=30)]
    
    feedback_notes = None
    final_drafts = []
    
    for attempt in range(max_revisions):
        logger.info(f"Generation attempt {attempt + 1}/{max_revisions} for topic {topic_id}")
        
        # A. Master Narrative
        narrative = generate_master_narrative(conn, pack, brand_context, model_route, feedback_notes)
        
        # B. Platform Adapters
        draft_li = adapt_for_linkedin(conn, narrative, brand_context, model_route)
        draft_x = adapt_for_x(conn, narrative, brand_context, model_route)
        draft_ig = adapt_for_instagram(conn, narrative, brand_context, model_route)
        
        drafts = [draft_li, draft_x, draft_ig]
        
        # C. Council
        council_fb = run_content_council(conn, drafts, pack, model_route)
        
        # D. Editor
        decision = evaluate_drafts(conn, council_fb, model_route)
        
        if decision.decision == "PASS":
            final_drafts = drafts
            break
        elif decision.decision == "REVISE":
            feedback_notes = decision.revision_notes
        else: # REJECT
            topic_repo.update_status(topic_id, TopicStatus.REJECTED.value)
            conn.commit()
            return False, ["Editor rejected drafts"]
            
    if not final_drafts:
        topic_repo.update_status(topic_id, TopicStatus.REJECTED.value)
        conn.commit()
        return False, ["Exceeded maximum revisions"]
        
    # E. Safety Checks
    for draft in final_drafts:
        is_safe = run_safety_checks(draft, past_posts, banned_phrases)
        if not is_safe:
            topic_repo.update_status(topic_id, TopicStatus.REJECTED.value)
            conn.commit()
            return False, ["Safety check failed (duplicate or banned phrase)"]
            
    # F. Save to DB
    import uuid
    # Create content_idea first to satisfy FK constraint
    cursor = conn.execute(
        "INSERT INTO content_ideas (topic_id, angle, status) VALUES (?, ?, ?)",
        (topic_id, narrative.core_thesis[:200], "APPROVED")
    )
    content_idea_id = cursor.lastrowid
    
    saved_ids = []
    for draft in final_drafts:
        post_id = post_repo.create({
            "content_idea_id": content_idea_id,
            "platform": draft.platform,
            "body": draft.text_content,
            "format": draft.format_type,
            "status": PostStatus.DRAFT.value,
            "idempotency_key": str(uuid.uuid4())
        })
        saved_ids.append(post_id)
        
    topic_repo.update_status(topic_id, TopicStatus.WRITTEN.value)
    conn.commit()
    
    return True, [f"Saved {len(saved_ids)} drafts to DB"]
