"""Reddit public JSON API adapter."""

from datetime import datetime, timezone
import logging
from typing import List
import requests

from hermes_social.constants import SourceType
from hermes_social.trends.base_adapter import SourceAdapter
from hermes_social.trends.models import RawCandidate

logger = logging.getLogger(__name__)


class RedditAdapter(SourceAdapter):
    """Adapter for Reddit public JSON endpoints."""

    def __init__(self, authority: float = 75.0, subreddits: List[str] = None, time_filter: str = "week") -> None:
        super().__init__(authority)
        self.subreddits = subreddits or ["MachineLearning", "webdev"]
        self.time_filter = time_filter
        # Reddit requires a custom User-Agent to avoid 429 Too Many Requests
        self.headers = {"User-Agent": "HermesSocialAgent/1.0.0 (TrendDiscovery)"}

    @property
    def source_type(self) -> str:
        return SourceType.REDDIT.value

    def fetch_candidates(self, limit: int = 30) -> List[RawCandidate]:
        """Fetch hot/top posts from configured subreddits."""
        candidates = []
        limit_per_sub = max(5, limit // len(self.subreddits))
        
        for sub in self.subreddits:
            url = f"https://www.reddit.com/r/{sub}/top.json"
            params = {"t": self.time_filter, "limit": limit_per_sub}
            
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch Reddit r/{sub}: {e}")
                continue
                
            posts = data.get("data", {}).get("children", [])
            for post_wrapper in posts:
                post = post_wrapper.get("data", {})
                
                # Skip stickied posts or empty titles
                if post.get("stickied") or not post.get("title"):
                    continue

                # URL is the external link if it exists, otherwise the reddit permalink
                post_url = post.get("url")
                permalink = f"https://www.reddit.com{post.get('permalink', '')}"
                
                # If the URL is just a reddit image or internal link, use permalink
                if not post_url or "reddit.com" in post_url or "redd.it" in post_url:
                    post_url = permalink

                published_at = None
                if post.get("created_utc"):
                    published_at = datetime.fromtimestamp(post["created_utc"], timezone.utc)

                candidate = RawCandidate(
                    title=post.get("title", ""),
                    url=post_url,
                    source_type=self.source_type,
                    source_name=f"Reddit (r/{sub})",
                    published_at=published_at,
                    discovered_at=datetime.now(timezone.utc),
                    excerpt=post.get("selftext", "")[:500],
                    tags=[sub],
                    engagement_signals={
                        "score": post.get("score", 0),
                        "comments": post.get("num_comments", 0),
                        "upvote_ratio": post.get("upvote_ratio", 0.0),
                    },
                    raw_url=permalink,
                )
                candidates.append(candidate)
                
        # Sort globally by score before returning
        candidates.sort(key=lambda c: c.engagement_signals.get("score", 0), reverse=True)
        return candidates[:limit]
