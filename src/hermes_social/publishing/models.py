"""Data models for the publishing layer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from hermes_social.constants import Platform


@dataclass
class PublishPayload:
    """Standardized payload passed to adapters for publishing."""
    platform: Platform
    text: str
    media_paths: List[str] = field(default_factory=list)
    hashtags: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    idempotency_key: Optional[str] = None


@dataclass
class PublishResult:
    """Result of a publishing attempt."""
    success: bool
    platform_post_id: Optional[str] = None
    platform_url: Optional[str] = None
    error: Optional[str] = None
    fallback_triggered: bool = False
