"""Knowledge Pack Builder."""

from typing import Dict, List

from hermes_social.constants import ClaimType, VerificationStatus
from hermes_social.research.models import ExtractedClaim, FetchedSource, KnowledgePack


def build_knowledge_pack(
    topic: Dict,
    sources: List[FetchedSource],
    claims: List[ExtractedClaim],
    research_run_id: int,
    confidence: float
) -> KnowledgePack:
    """Build a structured knowledge pack from research results."""
    
    # 1. Base Info
    canonical_topic = topic.get("canonical_topic", "Unknown Topic")
    why_now = f"Trend Velocity: {topic.get('trend_velocity', 0):.1f} | Freshness: High"
    audience_relevance = f"Pillar Match: {topic.get('content_pillar', 'None')} (Score: {topic.get('audience_relevance', 0):.1f})"
    
    # 2. Filter Claims
    verified_facts = [
        c.claim_text for c in claims 
        if c.verification_status == VerificationStatus.VERIFIED.value 
        and c.claim_type == ClaimType.FACT.value
    ]
    
    important_numbers = [
        c.claim_text for c in claims 
        if c.is_numerical and c.verification_status == VerificationStatus.VERIFIED.value
    ]
    
    opposing_views = [
        c.claim_text for c in claims 
        if c.claim_type == ClaimType.OPINION.value
    ]
    
    uncertainties = [
        c.claim_text for c in claims 
        if c.claim_type == ClaimType.PREDICTION.value 
        or c.confidence < 50.0
    ]
    
    what_people_get_wrong = [
        f"{c.claim_text} (Note: {c.contradiction_notes})" 
        for c in claims if c.verification_status == VerificationStatus.DISPUTED.value
    ]
    
    # 3. Context
    # Combine brief excerpts from the sources
    context_parts = []
    for s in sources:
        if s.fetch_status == "ok" and s.text_content:
            context_parts.append(f"- {s.text_content[:200]}...")
    context = "\n".join(context_parts) if context_parts else "No context extracted."
    
    # 4. Angles
    potential_angles = []
    if topic.get("unique_angle_score", 0) > 80.0:
        potential_angles.append("Strong Unique Angle Available (Low Saturation)")
    if topic.get("visual_potential", 0) > 50.0:
        potential_angles.append("High Visual Potential (Diagrams/Carousels recommended)")
        
    # 5. Source Map
    source_map = []
    for s in sources:
        claim_count = sum(1 for c in claims if s.url in c.source_urls)
        source_map.append({
            "url": s.url,
            "title": s.title,
            "authority": s.authority_score,
            "claims_count": claim_count,
            "status": s.fetch_status
        })
        
    return KnowledgePack(
        topic=canonical_topic,
        why_now=why_now,
        audience_relevance=audience_relevance,
        verified_facts=verified_facts,
        important_numbers=important_numbers,
        context=context,
        what_people_get_wrong=what_people_get_wrong,
        opposing_views=opposing_views,
        uncertainties=uncertainties,
        potential_angles=potential_angles,
        source_map=source_map,
        claims=claims,
        overall_confidence=confidence,
        research_run_id=research_run_id
    )
