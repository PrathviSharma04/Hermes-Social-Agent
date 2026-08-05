"""Registry for publishing adapters."""

from typing import Dict

from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from .base import PublisherAdapter
from .manual import ManualApprovalPublisher
from .linkedin import LinkedInPublisher
from .instagram import InstagramPublisher
from .x_publisher import XPublisher


def get_publisher(platform: Platform, config: AppConfig) -> PublisherAdapter:
    """
    Factory function to get the appropriate publishing adapter for a platform.
    If the platform is disabled, credentials are missing, or API is paid
    and paid APIs are disallowed, returns ManualApprovalPublisher.
    """
    
    # Check global publishing toggle
    if not getattr(config, "publishing_enabled", False):
        return ManualApprovalPublisher(config)
        
    # Instantiate the specific adapter
    if platform == Platform.LINKEDIN:
        adapter = LinkedInPublisher(config)
    elif platform == Platform.INSTAGRAM:
        adapter = InstagramPublisher(config)
    elif platform == Platform.X:
        adapter = XPublisher(config)
    else:
        return ManualApprovalPublisher(config)
        
    # Validate credentials; if invalid, fallback to manual
    if not adapter.validate_credentials():
        return ManualApprovalPublisher(config)
        
    return adapter


def validate_all_publishers(config: AppConfig) -> Dict[str, bool]:
    """Validate credentials for all supported platforms."""
    results = {}
    
    adapters = {
        "linkedin": LinkedInPublisher(config),
        "instagram": InstagramPublisher(config),
        "x": XPublisher(config)
    }
    
    for name, adapter in adapters.items():
        results[name] = adapter.validate_credentials()
        
    return results
