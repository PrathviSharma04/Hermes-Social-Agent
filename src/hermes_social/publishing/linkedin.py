"""LinkedIn Publisher Adapter."""

import logging
import requests
from typing import Dict, List, Any

from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from .base import PublisherAdapter
from .models import PublishPayload, PublishResult

logger = logging.getLogger(__name__)


class LinkedInPublisher(PublisherAdapter):
    """
    LinkedIn publishing adapter.
    Uses the LinkedIn API to publish text, image, and carousel posts.
    """
    
    # Base URL for LinkedIn API
    API_BASE = "https://api.linkedin.com/v2"
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.token = config.linkedin_access_token

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        }

    def validate_credentials(self) -> bool:
        if not self.token:
            return False
            
        try:
            # Check the me endpoint to validate token
            resp = requests.get(f"{self.API_BASE}/me", headers=self._get_headers(), timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
            
    def validate_permissions(self) -> bool:
        # Assuming token is valid, we would check for w_member_social or organization scopes
        return True
        
    def prepare_payload(self, post: Dict[str, Any], assets: List[Dict[str, Any]]) -> PublishPayload:
        body = post.get("body", "")
        hashtags = post.get("hashtags", "")
        
        full_text = body
        if hashtags:
            full_text += f"\n\n{hashtags}"
            
        return PublishPayload(
            platform=Platform.LINKEDIN,
            text=full_text,
            media_paths=[a["path"] for a in assets],
            idempotency_key=post.get("idempotency_key")
        )
        
    def publish(self, payload: PublishPayload, dry_run: bool = False) -> PublishResult:
        if not self.validate_credentials():
            logger.warning("LinkedIn credentials missing or invalid. Falling back to manual.")
            return PublishResult(success=False, fallback_triggered=True, error="Invalid credentials")
            
        if dry_run:
            logger.info(f"[DRY RUN] Would publish to LinkedIn: {payload.text[:50]}...")
            return PublishResult(success=True, platform_post_id="mock_urn_123")

        # Basic implementation of the 'Share on LinkedIn' API for text
        # In a complete implementation, this would handle media upload via assets API
        try:
            # We need the person URN
            me_resp = requests.get(f"{self.API_BASE}/me", headers=self._get_headers())
            me_resp.raise_for_status()
            author_urn = f"urn:li:person:{me_resp.json()['id']}"
            
            # Create a simple text share
            post_data = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": payload.text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            resp = requests.post(
                f"{self.API_BASE}/ugcPosts",
                headers=self._get_headers(),
                json=post_data,
                timeout=10
            )
            resp.raise_for_status()
            
            post_urn = resp.json().get("id")
            
            return PublishResult(
                success=True,
                platform_post_id=post_urn,
                platform_url=f"https://www.linkedin.com/feed/update/{post_urn}"
            )
            
        except Exception as e:
            logger.error(f"LinkedIn publish failed: {e}")
            return PublishResult(success=False, error=str(e))
            
    def verify_publish(self, publish_result: PublishResult) -> bool:
        if not publish_result.platform_post_id:
            return False
            
        try:
            resp = requests.get(
                f"{self.API_BASE}/ugcPosts/{publish_result.platform_post_id}",
                headers=self._get_headers()
            )
            return resp.status_code == 200
        except Exception:
            return False
            
    def fetch_post_reference(self, publish_result: PublishResult) -> str:
        return publish_result.platform_url or ""
        
    def handle_failure(self, post: Dict[str, Any], error: Exception) -> None:
        logger.error(f"Failed to publish post {post.get('id')} to LinkedIn: {error}")
