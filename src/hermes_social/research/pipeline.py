"""Research pipeline orchestrator."""

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from hermes_social.constants import TopicStatus, VerificationStatus
from hermes_social.db.repositories.research import ResearchRepository
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.research.claim_extractor import extract_claims
from hermes_social.research.claim_mapper import map_claims_to_sources
from hermes_social.research.confidence import compute_research_confidence
from hermes_social.research.contradiction_detector import detect_contradictions
from hermes_social.research.knowledge_pack import build_knowledge_pack
from hermes_social.research.models import KnowledgePack
from hermes_social.research.source_fetcher import fetch_all_sources
from hermes_social.research.vault_writer import write_knowledge_pack_to_vault

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    topic_id: int
    research_run_id: int
    knowledge_pack: KnowledgePack
    confidence: float
    claims_count: int
    verified_count: int
    disputed_count: int


def run_research_for_topic(
    conn: sqlite3.Connection,
    topic_id: int,
    vault_path: Path,
    dry_run: bool = False
) -> ResearchResult:
    """Execute the full research pipeline for a single topic."""
    
    topic_repo = TopicRepository(conn)
    research_repo = ResearchRepository(conn)
    
    # 1. Load topic and its sources from DB
    topic = topic_repo.get_by_id(topic_id)
    if not topic:
        raise ValueError(f"Topic {topic_id} not found")
        
    topic_sources = topic_repo.get_sources(topic_id)
    if not topic_sources:
        logger.warning(f"No sources found for topic {topic_id}")
        
    # 2. Create a research_run record
    if not dry_run:
        run_id = research_repo.create_run(topic_id, model_route="deterministic_v1")
    else:
        run_id = -1
        
    try:
        if not dry_run:
            topic_repo.update_status(topic_id, TopicStatus.RESEARCHING.value)
            
        # 3. Fetch actual web content for each source URL
        fetched_sources = fetch_all_sources(topic_sources)
        
        # 4. Extract claims from fetched content
        raw_claims = extract_claims(fetched_sources)
        
        # 5/6. Map claims back to sources (deduplicates and sets confidence/verification_status)
        mapped_claims = map_claims_to_sources(raw_claims, fetched_sources)
        
        # 7. Detect contradictions
        analyzed_claims = detect_contradictions(mapped_claims)
        
        # 8. Compute confidence score
        confidence = compute_research_confidence(analyzed_claims, fetched_sources)
        
        # 9. Build knowledge pack
        pack = build_knowledge_pack(topic, fetched_sources, analyzed_claims, run_id, confidence)
        
        if not dry_run:
            # 10. Persist claims and claim-source mappings to DB
            for claim in analyzed_claims:
                claim_data = {
                    "claim": claim.claim_text,
                    "claim_type": claim.claim_type,
                    "confidence": claim.confidence,
                    "verification_status": claim.verification_status,
                    "contradiction_status": claim.contradiction_notes,
                    "source_count": len(claim.source_ids)
                }
                claim_id = research_repo.add_claim(run_id, claim_data)
                
                # Link to sources
                for source_id in claim.source_ids:
                    research_repo.link_claim_source(claim_id, source_id)
                    
            # 11. Write knowledge pack to Obsidian vault
            write_knowledge_pack_to_vault(pack, vault_path)
            
            # 12. Complete the research_run
            research_repo.complete_run(run_id, confidence, f"Extracted {len(analyzed_claims)} claims.")
            
            # 13. Update topic status
            topic_repo.update_status(topic_id, TopicStatus.RESEARCHED.value)
            
            conn.commit()
            
        verified_count = sum(1 for c in analyzed_claims if c.verification_status == VerificationStatus.VERIFIED.value)
        disputed_count = sum(1 for c in analyzed_claims if c.verification_status == VerificationStatus.DISPUTED.value)
        
        return ResearchResult(
            topic_id=topic_id,
            research_run_id=run_id,
            knowledge_pack=pack,
            confidence=confidence,
            claims_count=len(analyzed_claims),
            verified_count=verified_count,
            disputed_count=disputed_count
        )
        
    except Exception as e:
        logger.error(f"Research run failed for topic {topic_id}: {e}")
        if not dry_run:
            research_repo.fail_run(run_id, str(e))
            topic_repo.update_status(topic_id, TopicStatus.REJECTED.value)
            conn.commit()
        raise
