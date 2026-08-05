"""Hacker News API adapter."""

from datetime import datetime, timezone
import logging
from typing import List, Optional
import requests

from hermes_social.constants import SourceType
from hermes_social.trends.base_adapter import SourceAdapter
from hermes_social.trends.models import RawCandidate

logger = logging.getLogger(__name__)


class HackerNewsAdapter(SourceAdapter):
    """Adapter for the public Hacker News Firebase API."""

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, authority: float = 88.0, min_score: int = 50) -> None:
        super().__init__(authority)
        self.min_score = min_score

    @property
    def source_type(self) -> str:
        return SourceType.HACKERNEWS.value

    def fetch_candidates(self, limit: int = 30) -> List[RawCandidate]:
        """Fetch top stories from Hacker News."""
        try:
            # Fetch top story IDs
            resp = requests.get(f"{self.BASE_URL}/topstories.json", timeout=10)
            resp.raise_for_status()
            story_ids = resp.json()[:100]  # Check top 100 to find `limit` good ones
        except requests.RequestException as e:
            logger.error(f"Failed to fetch HN top stories: {e}")
            return []

        candidates = []
        for story_id in story_ids:
            if len(candidates) >= limit:
                break
                
            story = self._fetch_story(story_id)
            if not story:
                continue
                
            # Filter by score
            score = story.get("score", 0)
            if score < self.min_score:
                continue
                
            # Must be a story with a URL (skip Ask HN for now, or handle differently)
            if story.get("type") != "story" or not story.get("url"):
                continue

            published_at = None
            if "time" in story:
                published_at = datetime.fromtimestamp(story["time"], timezone.utc)

            candidate = RawCandidate(
                title=story.get("title", ""),
                url=story.get("url", ""),
                source_type=self.source_type,
                source_name="Hacker News",
                published_at=published_at,
                discovered_at=datetime.now(timezone.utc),
                excerpt="",  # HN doesn't provide excerpts for link stories
                tags=[],
                engagement_signals={
                    "points": score,
                    "comments": story.get("descendants", 0),
                },
                raw_url=f"https://news.ycombinator.com/item?id={story_id}",
            )
            candidates.append(candidate)
            
        return candidates

    def _fetch_story(self, story_id: int) -> Optional[dict]:
        """Fetch details for a single HN story."""
        try:
            resp = requests.get(f"{self.BASE_URL}/item/{story_id}.json", timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch HN story {story_id}: {e}")
            return None
