"""Basic deterministic content-gap analysis (Section 9)."""

from typing import Dict, List

from hermes_social.trends.models import ScoredCandidate


def analyze_content_gap(
    candidate: ScoredCandidate,
    existing_topics: List[Dict],
    existing_posts: List[Dict],
) -> List[str]:
    """Perform basic heuristic content-gap analysis.
    
    Returns a list of content gap notes/angles.
    A trending topic without a useful angle (no gap) should be rejected later.
    (Full LLM-based analysis happens in Phase 5, this is the deterministic layer).
    """
    notes = []
    
    # 1. High Saturation Check
    if candidate.saturation > 80.0:
        notes.append("WARNING: High topic saturation detected in recent history.")
        
    # 2. Unique Angle Opportunity
    if candidate.unique_angle > 80.0:
        notes.append("Strong Opportunity: No recent coverage of this specific theme.")
        
    # 3. Engagement Velocity
    if candidate.trend_velocity > 80.0:
        notes.append("High Engagement: Topic is currently experiencing high velocity.")
        
    # 4. Pillar Alignment
    if candidate.matched_pillar:
        notes.append(f"Pillar Match: Aligns well with '{candidate.matched_pillar}'.")
    else:
        notes.append("WARNING: Does not strongly align with any content pillar.")

    # 5. Visual Potential
    if candidate.visual_potential > 50.0:
        notes.append("Visual Potential: Good candidate for carousel or diagram format.")

    # We attach these notes to the candidate
    candidate.content_gap_notes = notes
    
    return notes
