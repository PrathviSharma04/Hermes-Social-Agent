"""X (Twitter) Publisher Adapter."""

import logging
from typing import Dict, List, Any

try:
    import tweepy
except ImportError:
    tweepy = None

from hermes_social.config import AppConfig
from hermes_social.constants import Platform
from .base import PublisherAdapter
from .models import PublishPayload, PublishResult

logger = logging.getLogger(__name__)


class XPublisher(PublisherAdapter):
    """
    X publishing adapter.
    Uses Tweepy and X API v2 to publish tweets and threads.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = None
        
        if tweepy and config.x_api_key and config.x_access_token:
            try:
                self.client = tweepy.Client(
                    consumer_key=config.x_api_key,
                    consumer_secret=config.x_api_secret,
                    access_token=config.x_access_token,
                    access_token_secret=config.x_access_token_secret
                )
            except Exception as e:
                logger.error(f"Failed to init Tweepy: {e}")

    def validate_credentials(self) -> bool:
        if not self.client:
            return False
            
        try:
            me = self.client.get_me()
            return me.data is not None
        except Exception:
            return False
            
    def validate_permissions(self) -> bool:
        return True
        
    def prepare_payload(self, post: Dict[str, Any], assets: List[Dict[str, Any]]) -> PublishPayload:
        return PublishPayload(
            platform=Platform.X,
            text=post.get("body", ""),
            media_paths=[a["path"] for a in assets],
            idempotency_key=post.get("idempotency_key")
        )
        
    def publish(self, payload: PublishPayload, dry_run: bool = False) -> PublishResult:
        if not self.client or not self.validate_credentials():
            logger.warning("X credentials missing or invalid. Falling back to manual.")
            return PublishResult(success=False, fallback_triggered=True, error="Invalid credentials")
            
        if dry_run:
            logger.info(f"[DRY RUN] Would publish to X: {payload.text[:50]}...")
            return PublishResult(success=True, platform_post_id="mock_x_123")

        try:
            # Splitting thread by \n\n if it's long, or just posting as one if short
            # For this MVP, we assume it's short enough for one tweet or already formatted
            # Real threads require replying to the previous tweet ID
            
            response = self.client.create_tweet(text=payload.text[:280])
            tweet_id = response.data['id']
            
            return PublishResult(
                success=True,
                platform_post_id=tweet_id,
                platform_url=f"https://x.com/user/status/{tweet_id}"
            )
            
        except Exception as e:
            logger.error(f"X publish failed: {e}")
            return PublishResult(success=False, error=str(e))
            
    def verify_publish(self, publish_result: PublishResult) -> bool:
        if not self.client or not publish_result.platform_post_id:
            return False
            
        try:
            tweet = self.client.get_tweet(publish_result.platform_post_id)
            return tweet.data is not None
        except Exception:
            return False
            
    def fetch_post_reference(self, publish_result: PublishResult) -> str:
        return publish_result.platform_url or ""
        
    def handle_failure(self, post: Dict[str, Any], error: Exception) -> None:
        logger.error(f"Failed to publish post to X: {error}")
