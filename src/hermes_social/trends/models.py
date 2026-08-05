"""Data models for the trend discovery pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class RawCandidate:
    """A raw trend candidate discovered from a source, before scoring."""
    title: str
    url: str
    source_type: str          # "rss", "hackernews", "devto", "reddit"
    source_name: str          # "Hacker News", "Dev.to", etc.
    published_at: Optional[datetime]
    discovered_at: datetime
    excerpt: str              # First ~500 chars of content
    tags: List[str]           # Source-provided tags/categories
    engagement_signals: Dict[str, Any]  # {"points": 150, "comments": 42} etc.
    raw_url: str              # Original source URL


@dataclass
class ScoredCandidate:
    """A candidate after opportunity scoring and content-gap analysis."""
    candidate: RawCandidate
    freshness: float          # 0-100
    trend_velocity: float     # 0-100
    audience_relevance: float # 0-100
    source_authority: float   # 0-100
    unique_angle: float       # 0-100
    visual_potential: float   # 0-100
    pillar_fit: float         # 0-100
    saturation: float         # 0-100
    opportunity_score: float  # Composite weighted score
    matched_pillar: Optional[str]
    content_gap_notes: List[str] = field(default_factory=list)
    rejection_reason: Optional[str] = None  # None if accepted
