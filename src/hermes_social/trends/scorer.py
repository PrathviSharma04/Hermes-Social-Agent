"""Opportunity scoring logic (Section 9 formula)."""

import math
from typing import Dict, List

from hermes_social.services.brand import BrandSystem
from hermes_social.trends.freshness import compute_freshness
from hermes_social.trends.models import RawCandidate, ScoredCandidate


def score_candidates(
    candidates: List[RawCandidate],
    brand: BrandSystem,
    weights: Dict[str, float],
    existing_topics: List[Dict],
    source_configs: Dict,
) -> List[ScoredCandidate]:
    """Score all candidates and return sorted by opportunity_score DESC."""
    scored = []
    
    # Pre-compute some DB stats for saturation/unique angle
    # In a real system, we'd check recent topics. Here we use a heuristic based on existing_topics.
    recent_titles = [t.get("canonical_topic", "").lower() for t in existing_topics]

    for candidate in candidates:
        scored.append(_score_single(candidate, brand, weights, recent_titles, source_configs))
        
    scored.sort(key=lambda x: x.opportunity_score, reverse=True)
    return scored


def _score_single(
    candidate: RawCandidate,
    brand: BrandSystem,
    weights: Dict[str, float],
    recent_titles: List[str],
    source_configs: Dict,
) -> ScoredCandidate:
    """Score a single candidate using the multi-factor opportunity formula."""
    
    # 1. Freshness (0-100)
    freshness = compute_freshness(candidate.published_at, max_age_hours=72)
    
    # 2. Trend Velocity (0-100)
    # Heuristic based on engagement signals
    velocity = 0.0
    sig = candidate.engagement_signals
    if candidate.source_type == "hackernews":
        # HN: 100 points ~ 50%, 500+ points ~ 100%
        pts = sig.get("points", 0)
        velocity = min(100.0, (pts / 500.0) * 100.0)
    elif candidate.source_type == "reddit":
        # Reddit: 500 score ~ 50%, 2000+ ~ 100%
        score = sig.get("score", 0)
        velocity = min(100.0, (score / 2000.0) * 100.0)
    elif candidate.source_type == "devto":
        # DevTo: 50 reactions ~ 50%, 200+ ~ 100%
        reacts = sig.get("reactions", 0)
        velocity = min(100.0, (reacts / 200.0) * 100.0)
    else:
        # Default velocity for RSS or unknown
        velocity = 50.0

    # 3. Audience Relevance & Pillar Fit (0-100)
    # Check text against pillar keywords
    text_to_check = f"{candidate.title} {candidate.excerpt} {' '.join(candidate.tags)}".lower()
    
    pillar_fit = 0.0
    audience_relevance = 0.0
    matched_pillar = None
    
    for pillar in brand.content_pillars:
        matches = sum(1 for kw in pillar.keywords if kw.lower() in text_to_check)
        if matches > 0:
            # Found a match!
            if pillar_fit == 0:
                matched_pillar = pillar.name
            # Score based on number of matches, up to 100
            score = min(100.0, matches * 33.3)
            pillar_fit = max(pillar_fit, score)
            audience_relevance = max(audience_relevance, score)

    # 4. Source Authority (0-100)
    # Lookup in config, fallback to 50
    authority = 50.0
    if candidate.source_type == "rss":
        for feed in source_configs.get("rss_feeds", []):
            if feed.get("name") == candidate.source_name:
                authority = float(feed.get("authority", 80))
                break
    elif candidate.source_type in source_configs:
        authority = float(source_configs[candidate.source_type].get("authority", 50))

    # 5. Visual Potential (0-100)
    visual_keywords = ["design", "ui", "ux", "frontend", "css", "architecture", "diagram", "chart", "data"]
    visual_matches = sum(1 for kw in visual_keywords if kw in text_to_check)
    visual_potential = min(100.0, visual_matches * 50.0)

    # 6. Saturation & Unique Angle (0-100)
    # Check how many recent DB topics share words with this candidate's title
    words = set(w for w in candidate.title.lower().split() if len(w) > 4)
    saturation_count = 0
    for rt in recent_titles:
        rt_words = set(w for w in rt.split() if len(w) > 4)
        if len(words.intersection(rt_words)) >= 2:
            saturation_count += 1
            
    # Max saturation at 5 similar posts
    saturation = min(100.0, (saturation_count / 5.0) * 100.0)
    # Unique angle is inversely proportional to saturation
    unique_angle = 100.0 - saturation

    # Calculate final composite score
    # Formula from Section 9: Freshness * Velocity * Relevance * Authority * Unique * Visual * Pillar * (1 - Saturation)
    # Since multiplying probabilities is harsh, we use a weighted sum approach based on the weights config
    
    # Normalize weights so they sum to 1.0 (just in case)
    total_weight = sum(weights.values())
    w = {k: v / total_weight for k, v in weights.items()}
    
    opportunity_score = (
        (freshness * w.get("freshness", 0.15)) +
        (velocity * w.get("trend_velocity", 0.15)) +
        (audience_relevance * w.get("audience_relevance", 0.20)) +
        (authority * w.get("source_authority", 0.10)) +
        (unique_angle * w.get("unique_angle", 0.15)) +
        (visual_potential * w.get("visual_potential", 0.05)) +
        (pillar_fit * w.get("pillar_fit", 0.15))
    )
    
    # Apply saturation penalty directly
    opportunity_score = opportunity_score * (1.0 - (saturation / 100.0) * w.get("saturation_penalty", 0.05))

    return ScoredCandidate(
        candidate=candidate,
        freshness=freshness,
        trend_velocity=velocity,
        audience_relevance=audience_relevance,
        source_authority=authority,
        unique_angle=unique_angle,
        visual_potential=visual_potential,
        pillar_fit=pillar_fit,
        saturation=saturation,
        opportunity_score=opportunity_score,
        matched_pillar=matched_pillar,
    )
