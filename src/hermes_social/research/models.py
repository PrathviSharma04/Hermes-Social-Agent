"""Data models for the research and fact-checking pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class FetchedSource:
    """A web page fetched and parsed during research."""
    url: str
    title: str
    text_content: str          # Extracted plain text
    published_at: Optional[datetime]
    fetch_status: str          # "ok", "error", "timeout"
    authority_score: float
    source_id: int             # DB ID from topic_sources


@dataclass
class ExtractedClaim:
    """A claim extracted from source text."""
    claim_text: str
    claim_type: str            # FACT, OPINION, PREDICTION, PERSONAL_EXPERIENCE
    source_urls: List[str]     # Which source URLs this claim appeared in
    source_ids: List[int]      # Which DB source IDs this claim appeared in
    confidence: float          # 0-100
    is_numerical: bool         # Contains a specific number/statistic
    verification_status: str   # UNVERIFIED, VERIFIED, DISPUTED
    contradiction_notes: Optional[str] = None


@dataclass
class KnowledgePack:
    """The complete research output for a topic (Section 10 format)."""
    topic: str
    why_now: str
    audience_relevance: str
    verified_facts: List[str]
    important_numbers: List[str]
    context: str
    what_people_get_wrong: List[str]
    opposing_views: List[str]
    uncertainties: List[str]
    potential_angles: List[str]
    source_map: List[Dict[str, Any]]     # [{url, title, authority, claims_count}]
    claims: List[ExtractedClaim]
    overall_confidence: float
    research_run_id: int
