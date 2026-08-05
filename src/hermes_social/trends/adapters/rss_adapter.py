"""RSS feed source adapter."""

from datetime import datetime, timezone
import logging
from time import mktime
from typing import Any, Dict, List, Optional
import feedparser

from hermes_social.constants import SourceType
from hermes_social.trends.base_adapter import SourceAdapter
from hermes_social.trends.models import RawCandidate

logger = logging.getLogger(__name__)


class RSSAdapter(SourceAdapter):
    """Adapter for generic RSS/Atom feeds."""

    def __init__(self, feed_configs: List[Dict[str, str]]) -> None:
        """Initialize with a list of feed configurations (name, url, authority)."""
        # Overall authority is not strictly used for RSS since each feed has its own,
        # but we set a default to satisfy the base class.
        super().__init__(authority=80.0)
        self.feed_configs = feed_configs

    @property
    def source_type(self) -> str:
        return SourceType.RSS.value

    def fetch_candidates(self, limit: int = 30) -> List[RawCandidate]:
        """Fetch candidates from all configured RSS feeds."""
        candidates = []
        for config in self.feed_configs:
            name = config.get("name", "Unknown RSS")
            url = config.get("url")
            authority = float(config.get("authority", self.authority_score))
            
            if not url:
                continue
                
            logger.info(f"Fetching RSS feed: {name} ({url})")
            try:
                # Limit parsing per feed to leave room for others
                feed_limit = max(5, limit // len(self.feed_configs))
                feed_candidates = self._fetch_feed(name, url, feed_limit)
                # Override authority for this specific feed via a pseudo-signal if needed,
                # though currently authority is handled in scoring via source config.
                candidates.extend(feed_candidates)
            except Exception as e:
                logger.error(f"Error fetching RSS feed {name}: {e}")
                
        return candidates[:limit]

    def _fetch_feed(self, source_name: str, url: str, limit: int) -> List[RawCandidate]:
        """Fetch and parse a single RSS feed."""
        feed = feedparser.parse(url)
        candidates = []
        
        for entry in feed.entries[:limit]:
            published_at = self._parse_date(entry)
            
            # Extract tags/categories
            tags = []
            if hasattr(entry, "tags"):
                tags = [t.term for t in entry.tags if hasattr(t, "term")]
                
            # Extract excerpt
            excerpt = ""
            if hasattr(entry, "summary"):
                excerpt = entry.summary[:500]
            elif hasattr(entry, "description"):
                excerpt = entry.description[:500]

            candidate = RawCandidate(
                title=entry.get("title", "").strip(),
                url=entry.get("link", ""),
                source_type=self.source_type,
                source_name=source_name,
                published_at=published_at,
                discovered_at=datetime.now(timezone.utc),
                excerpt=excerpt,
                tags=tags,
                engagement_signals={},  # RSS rarely has standard engagement metrics
                raw_url=entry.get("link", ""),
            )
            
            # Skip invalid entries
            if candidate.title and candidate.url:
                candidates.append(candidate)
                
        return candidates

    def _parse_date(self, entry: Any) -> Optional[datetime]:
        """Parse RSS date into timezone-aware UTC datetime."""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                return dt
            except (ValueError, TypeError, OverflowError):
                pass
        return None
