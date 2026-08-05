"""Discovery pipeline orchestrator."""

import logging
import sqlite3
from dataclasses import dataclass
from typing import Dict, List

from hermes_social.services.brand import BrandSystem
from hermes_social.trends.adapters.devto_adapter import DevToAdapter
from hermes_social.trends.adapters.hackernews_adapter import HackerNewsAdapter
from hermes_social.trends.adapters.reddit_adapter import RedditAdapter
from hermes_social.trends.adapters.rss_adapter import RSSAdapter
from hermes_social.trends.dedup import deduplicate_candidates
from hermes_social.trends.freshness import filter_stale
from hermes_social.trends.gap_analyzer import analyze_content_gap
from hermes_social.trends.models import ScoredCandidate
from hermes_social.trends.normalizer import normalize_candidates
from hermes_social.trends.scorer import score_candidates

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryResult:
    """Result of a single discovery cycle."""
    total_fetched: int
    after_dedup: int
    after_freshness: int
    scored: int
    accepted: int
    rejected: int
    candidates: List[ScoredCandidate]


def run_discovery_cycle(
    conn: sqlite3.Connection,
    brand: BrandSystem,
    sources_config: Dict,
    min_opportunity_score: float = 50.0,
    dry_run: bool = False,
) -> DiscoveryResult:
    """Execute a full trend discovery cycle."""
    
    # 1. Initialize Adapters
    adapters = []
    
    if sources_config.get("rss_feeds"):
        adapters.append(RSSAdapter(sources_config["rss_feeds"]))
        
    hn_cfg = sources_config.get("hackernews", {})
    if hn_cfg.get("enabled"):
        adapters.append(HackerNewsAdapter(
            authority=hn_cfg.get("authority", 88.0),
            min_score=hn_cfg.get("min_score", 50)
        ))
        
    devto_cfg = sources_config.get("devto", {})
    if devto_cfg.get("enabled"):
        adapters.append(DevToAdapter(
            authority=devto_cfg.get("authority", 70.0),
            tags=devto_cfg.get("tags")
        ))
        
    reddit_cfg = sources_config.get("reddit", {})
    if reddit_cfg.get("enabled"):
        adapters.append(RedditAdapter(
            authority=reddit_cfg.get("authority", 75.0),
            subreddits=reddit_cfg.get("subreddits"),
            time_filter=reddit_cfg.get("time_filter", "week")
        ))

    # 2. Fetch Raw Candidates
    raw_candidates = []
    for adapter in adapters:
        try:
            logger.info(f"Fetching from {adapter.source_type}...")
            cands = adapter.fetch_candidates(limit=30)
            raw_candidates.extend(cands)
            logger.info(f"Fetched {len(cands)} candidates from {adapter.source_type}")
        except Exception as e:
            logger.error(f"Error fetching from {adapter.source_type}: {e}")
            
    total_fetched = len(raw_candidates)

    # 3. Normalize
    normalized = normalize_candidates(raw_candidates)
    
    # Fetch existing topics from DB for dedup/scoring
    cursor = conn.execute("SELECT id, canonical_topic FROM topics ORDER BY id DESC LIMIT 500")
    existing_topics = [{"id": row[0], "canonical_topic": row[1]} for row in cursor.fetchall()]

    # 4. Deduplicate
    deduped = deduplicate_candidates(normalized, existing_topics)
    after_dedup = len(deduped)
    
    # 5. Filter Stale
    fresh = filter_stale(deduped)
    after_freshness = len(fresh)
    
    # 6. Score
    weights = sources_config.get("scoring_weights", {})
    scored = score_candidates(fresh, brand, weights, existing_topics, sources_config)
    
    # 7. Gap Analysis & Acceptance Filtering
    accepted_candidates = []
    accepted = 0
    rejected = 0
    
    for sc in scored:
        analyze_content_gap(sc, existing_topics, [])
        
        # Check acceptance criteria
        if sc.opportunity_score < min_opportunity_score:
            sc.rejection_reason = f"Score below threshold ({sc.opportunity_score:.1f} < {min_opportunity_score})"
            rejected += 1
        elif not sc.matched_pillar:
            sc.rejection_reason = "No content pillar match"
            rejected += 1
        else:
            accepted += 1
            accepted_candidates.append(sc)

    # 8. Insert to DB if not dry run
    if not dry_run and accepted_candidates:
        from hermes_social.db.repositories.topics import TopicRepository
        repo = TopicRepository(conn)
        
        for sc in accepted_candidates:
            topic_data = {
                "canonical_topic": sc.candidate.title,
                "summary": sc.candidate.excerpt,
                "category": sc.candidate.source_type,
                "content_pillar": sc.matched_pillar,
                "trend_velocity": sc.trend_velocity,
                "audience_relevance": sc.audience_relevance,
                "saturation_score": sc.saturation,
                "unique_angle_score": sc.unique_angle,
                "visual_potential": sc.visual_potential,
                "source_authority": sc.source_authority,
                "opportunity_score": sc.opportunity_score,
                "status": "DISCOVERED"
            }
            try:
                topic_id = repo.create(topic_data)
                
                # Add source
                source_data = {
                    "source_type": sc.candidate.source_type,
                    "source_name": sc.candidate.source_name,
                    "url": sc.candidate.raw_url,
                    "published_at": sc.candidate.published_at,
                    "authority_score": sc.source_authority,
                    "raw_excerpt_hash": None,
                    "notes": "\n".join(sc.content_gap_notes)
                }
                repo.add_source(topic_id, source_data)
                
            except Exception as e:
                logger.error(f"Failed to insert topic '{sc.candidate.title}': {e}")
                
        conn.commit()

    return DiscoveryResult(
        total_fetched=total_fetched,
        after_dedup=after_dedup,
        after_freshness=after_freshness,
        scored=len(scored),
        accepted=accepted,
        rejected=rejected,
        candidates=scored  # Return all scored, even rejected, for inspection
    )
