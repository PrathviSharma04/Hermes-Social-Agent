"""Registry for metric collectors."""

from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from .collectors import (
    MetricCollector,
    LinkedInCollector,
    InstagramCollector,
    XCollector,
    MockCollector
)

def get_collector(platform: Platform, config: AppConfig) -> MetricCollector:
    """Return the appropriate metric collector for the platform."""
    
    # If the user has live API tokens with the necessary scopes, we use the real ones.
    # Otherwise, we gracefully fall back to MockCollector to keep the data pipeline working.
    
    if platform == Platform.LINKEDIN and config.linkedin_access_token:
        # Checking for read analytics scopes would ideally happen here
        return LinkedInCollector(config)
        
    elif platform == Platform.INSTAGRAM and config.instagram_access_token:
        return InstagramCollector(config)
        
    elif platform == Platform.X and config.x_access_token:
        return XCollector(config)
        
    # Default fallback for testing or missing APIs
    return MockCollector(config)
