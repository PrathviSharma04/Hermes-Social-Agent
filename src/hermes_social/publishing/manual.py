"""Manual Fallback Publisher Adapter."""

import logging
from typing import Dict, List, Any

from hermes_social.config import AppConfig
from hermes_social.constants import PostStatus
from .base import PublisherAdapter
from .models import PublishPayload, PublishResult

logger = logging.getLogger(__name__)


class ManualApprovalPublisher(PublisherAdapter):
    """
    Fallback adapter used when API access is missing, unauthorized, or paid.
    Instead of publishing, it transitions the post to READY_FOR_MANUAL_PUBLISH.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config

    def validate_credentials(self) -> bool:
        """Manual publishing requires no credentials."""
        return True
        
    def validate_permissions(self) -> bool:
        return True
        
    def prepare_payload(self, post: Dict[str, Any], assets: List[Dict[str, Any]]) -> PublishPayload:
        from hermes_social.constants import Platform
        try:
            platform = Platform(post["platform"])
        except ValueError:
            platform = Platform.LINKEDIN
            
        return PublishPayload(
            platform=platform,
            text=post.get("body", ""),
            media_paths=[a["path"] for a in assets],
            hashtags=post.get("hashtags"),
            idempotency_key=post.get("idempotency_key")
        )
        
    def publish(self, payload: PublishPayload, dry_run: bool = False) -> PublishResult:
        if dry_run:
            logger.info(f"[DRY RUN] Manual Fallback for {payload.platform.value}")
            return PublishResult(success=True, fallback_triggered=True)
            
        logger.info(f"Triggering manual fallback for {payload.platform.value} post.")
        
        # In a full system, this would also trigger a Telegram notification
        # containing the assets and text for the user to copy-paste.
        
        return PublishResult(
            success=False, 
            error="API publishing not configured. Please publish manually.",
            fallback_triggered=True
        )
        
    def verify_publish(self, publish_result: PublishResult) -> bool:
        return False
        
    def fetch_post_reference(self, publish_result: PublishResult) -> str:
        return ""
        
    def handle_failure(self, post: Dict[str, Any], error: Exception) -> None:
        pass
