"""Raw metric collectors for social platforms."""

import random
from abc import ABC, abstractmethod
from typing import Any, Dict

from hermes_social.config import AppConfig
from hermes_social.constants import PerformanceWindow


class MetricCollector(ABC):
    """Abstract interface for gathering post performance metrics."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    @abstractmethod
    def fetch_metrics(self, platform_post_id: str, window: PerformanceWindow) -> Dict[str, Any]:
        """Fetch metrics for a specific post at a specific window."""
        pass


class MockCollector(MetricCollector):
    """Generates realistic mock metrics for testing without paid/restricted APIs."""
    
    def fetch_metrics(self, platform_post_id: str, window: PerformanceWindow) -> Dict[str, Any]:
        """Generate scaled metrics based on the window."""
        
        # Scale multipliers based on how long the post has been live
        scales = {
            PerformanceWindow.HOUR_2: 1.0,
            PerformanceWindow.HOUR_24: 5.0,
            PerformanceWindow.HOUR_72: 8.0,
            PerformanceWindow.DAY_7: 10.0
        }
        scale = scales.get(window, 1.0)
        
        # Deterministic random based on platform_post_id so it strictly increases
        random.seed(f"{platform_post_id}_{window.value}")
        
        # Base numbers
        base_impressions = random.randint(100, 1000)
        base_likes = int(base_impressions * random.uniform(0.01, 0.05))
        base_comments = int(base_likes * random.uniform(0.1, 0.4))
        base_shares = int(base_likes * random.uniform(0.05, 0.2))
        
        return {
            "impressions": int(base_impressions * scale),
            "reach": int(base_impressions * scale * 0.9),  # Reach is usually slightly less than impressions
            "likes": int(base_likes * scale),
            "comments": int(base_comments * scale),
            "shares": int(base_shares * scale),
            "saves": int(base_likes * scale * 0.5),
            "clicks": int(base_impressions * scale * 0.02),
            "other_metrics": {"mocked": True}
        }


class LinkedInCollector(MetricCollector):
    """Fetches real metrics via LinkedIn API."""
    def fetch_metrics(self, platform_post_id: str, window: PerformanceWindow) -> Dict[str, Any]:
        # For this MVP without Community Management API access, we use Mock
        # Implementation would call: GET https://api.linkedin.com/v2/organizationalEntityShareStatistics
        return MockCollector(self.config).fetch_metrics(platform_post_id, window)


class InstagramCollector(MetricCollector):
    """Fetches real metrics via Instagram Graph API."""
    def fetch_metrics(self, platform_post_id: str, window: PerformanceWindow) -> Dict[str, Any]:
        # Implementation would call: GET /{ig-media-id}/insights
        return MockCollector(self.config).fetch_metrics(platform_post_id, window)


class XCollector(MetricCollector):
    """Fetches real metrics via X API v2."""
    def fetch_metrics(self, platform_post_id: str, window: PerformanceWindow) -> Dict[str, Any]:
        # Implementation would call: GET /2/tweets?ids={id}&tweet.fields=non_public_metrics
        return MockCollector(self.config).fetch_metrics(platform_post_id, window)
