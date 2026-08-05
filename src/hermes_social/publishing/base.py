"""Abstract base class for publishing adapters."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

from .models import PublishResult, PublishPayload


class PublisherAdapter(ABC):
    """
    Abstract interface for publishing content to a social platform.
    Implementations should handle format-specific adaptations and API integration.
    """
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Check if required API credentials exist and are valid."""
        pass
        
    @abstractmethod
    def validate_permissions(self) -> bool:
        """Check if the authenticated user has permission to post."""
        pass
        
    @abstractmethod
    def prepare_payload(self, post: Dict[str, Any], assets: List[Dict[str, Any]]) -> PublishPayload:
        """Transform internal DB representations into a platform-agnostic PublishPayload."""
        pass
        
    @abstractmethod
    def publish(self, payload: PublishPayload, dry_run: bool = False) -> PublishResult:
        """
        Execute the publish action via the platform's API.
        If dry_run is True, validate the payload but do not send the final POST request.
        """
        pass
        
    @abstractmethod
    def verify_publish(self, publish_result: PublishResult) -> bool:
        """Verify the post was actually published by checking the platform post ID."""
        pass
        
    @abstractmethod
    def fetch_post_reference(self, publish_result: PublishResult) -> str:
        """Return the public URL of the published post."""
        pass
        
    @abstractmethod
    def handle_failure(self, post: Dict[str, Any], error: Exception) -> None:
        """Execute fallback/cleanup logic when publishing fails."""
        pass
