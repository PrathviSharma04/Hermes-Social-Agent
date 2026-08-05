"""Instagram Publisher Adapter."""

import logging
import requests
from typing import Dict, List, Any

from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from .base import PublisherAdapter
from .models import PublishPayload, PublishResult

logger = logging.getLogger(__name__)


class InstagramPublisher(PublisherAdapter):
    """
    Instagram publishing adapter via Facebook Graph API.
    """
    
    API_BASE = "https://graph.facebook.com/v19.0"
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.token = config.instagram_access_token
        self.account_id = config.instagram_account_id

    def validate_credentials(self) -> bool:
        if not self.token or not self.account_id:
            return False
            
        try:
            resp = requests.get(
                f"{self.API_BASE}/{self.account_id}",
                params={"access_token": self.token},
                timeout=5
            )
            return resp.status_code == 200
        except Exception:
            return False
            
    def validate_permissions(self) -> bool:
        return True
        
    def prepare_payload(self, post: Dict[str, Any], assets: List[Dict[str, Any]]) -> PublishPayload:
        return PublishPayload(
            platform=Platform.INSTAGRAM,
            text=post.get("body", ""),
            media_paths=[a["path"] for a in assets],
            idempotency_key=post.get("idempotency_key")
        )
        
    def publish(self, payload: PublishPayload, dry_run: bool = False) -> PublishResult:
        if not self.validate_credentials():
            return PublishResult(success=False, fallback_triggered=True, error="Invalid credentials")
            
        if dry_run:
            logger.info(f"[DRY RUN] Would publish to Instagram: {payload.text[:50]}...")
            return PublishResult(success=True, platform_post_id="mock_ig_123")

        # Mocking actual implementation for now as it requires complex image hosting
        # Instagram Graph API requires images to be public URLs before uploading
        return PublishResult(
            success=False,
            error="Instagram automated publish requires public image URLs. Falling back to manual.",
            fallback_triggered=True
        )
            
    def verify_publish(self, publish_result: PublishResult) -> bool:
        return False
            
    def fetch_post_reference(self, publish_result: PublishResult) -> str:
        return ""
        
    def handle_failure(self, post: Dict[str, Any], error: Exception) -> None:
        logger.error(f"Failed to publish post to Instagram: {error}")
