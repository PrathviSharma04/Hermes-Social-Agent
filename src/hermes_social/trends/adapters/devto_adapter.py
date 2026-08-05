"""Dev.to public API adapter."""

from datetime import datetime, timezone
import logging
from typing import List
import requests
from dateutil import parser as date_parser

from hermes_social.constants import SourceType
from hermes_social.trends.base_adapter import SourceAdapter
from hermes_social.trends.models import RawCandidate

logger = logging.getLogger(__name__)


class DevToAdapter(SourceAdapter):
    """Adapter for the public Dev.to API."""

    BASE_URL = "https://dev.to/api/articles"

    def __init__(self, authority: float = 70.0, tags: List[str] = None) -> None:
        super().__init__(authority)
        self.tags = tags or ["ai", "webdev", "programming"]

    @property
    def source_type(self) -> str:
        return SourceType.DEVTO.value

    def fetch_candidates(self, limit: int = 30) -> List[RawCandidate]:
        """Fetch trending articles from Dev.to based on tags."""
        candidates = []
        
        # We fetch a few pages or state to get enough candidates across tags
        # The Dev.to API supports comma-separated tags, but we'll request a bit broader
        tags_str = ",".join(self.tags[:5])  # Max 5 tags for query
        params = {
            "tags": tags_str,
            "top": 7,  # Top articles in the last 7 days
            "per_page": limit * 2,  # Fetch more to allow filtering
        }
        
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            articles = resp.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Dev.to articles: {e}")
            return []

        for article in articles:
            if len(candidates) >= limit:
                break
                
            published_at = None
            if article.get("published_at"):
                try:
                    published_at = date_parser.parse(article["published_at"])
                    # Ensure it's UTC
                    if published_at.tzinfo is None:
                        published_at = published_at.replace(tzinfo=timezone.utc)
                except Exception:
                    pass

            candidate = RawCandidate(
                title=article.get("title", ""),
                url=article.get("url", ""),
                source_type=self.source_type,
                source_name="Dev.to",
                published_at=published_at,
                discovered_at=datetime.now(timezone.utc),
                excerpt=article.get("description", "")[:500],
                tags=article.get("tag_list", []),
                engagement_signals={
                    "reactions": article.get("public_reactions_count", 0),
                    "comments": article.get("comments_count", 0),
                },
                raw_url=article.get("url", ""),
            )
            
            if candidate.title and candidate.url:
                candidates.append(candidate)
                
        return candidates
