"""Confirmation policy engine for destructive Telegram actions."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from hermes_social.constants import TelegramIntent
from .intents import ParsedIntent


# Intents that require explicit user confirmation per Section 21
DESTRUCTIVE_INTENTS: Set[TelegramIntent] = {
    TelegramIntent.CANCEL_POST,
    TelegramIntent.EMERGENCY_STOP,
    TelegramIntent.PAUSE_AUTOPILOT,
    TelegramIntent.RESUME_AUTOPILOT,
    TelegramIntent.PAUSE_PUBLISHING,
    TelegramIntent.RESUME_PUBLISHING
}


@dataclass
class PendingConfirmation:
    """A pending destructive action waiting for user confirmation."""
    action_id: str
    intent: ParsedIntent
    expires_at: datetime


class ConfirmationManager:
    """Manages short-lived confirmation tokens for Telegram actions."""
    
    def __init__(self, expiry_minutes: int = 15):
        self._pending: Dict[str, PendingConfirmation] = {}
        self.expiry_minutes = expiry_minutes

    def requires_confirmation(self, intent: TelegramIntent) -> bool:
        """Check if an intent requires explicit confirmation."""
        return intent in DESTRUCTIVE_INTENTS

    def create_pending(self, parsed_intent: ParsedIntent) -> PendingConfirmation:
        """Create a new pending confirmation."""
        action_id = str(uuid.uuid4())[:8]  # Short ID for inline callbacks
        expires_at = datetime.now() + timedelta(minutes=self.expiry_minutes)
        
        pending = PendingConfirmation(
            action_id=action_id,
            intent=parsed_intent,
            expires_at=expires_at
        )
        self._pending[action_id] = pending
        self.cleanup_expired()
        return pending

    def confirm(self, action_id: str) -> Optional[ParsedIntent]:
        """Confirm an action and return the original intent for execution."""
        self.cleanup_expired()
        pending = self._pending.pop(action_id, None)
        if pending:
            return pending.intent
        return None

    def cancel(self, action_id: str) -> None:
        """Cancel a pending action."""
        self._pending.pop(action_id, None)

    def cleanup_expired(self) -> int:
        """Remove expired confirmations to prevent memory leaks."""
        now = datetime.now()
        expired_keys = [
            k for k, v in self._pending.items() if v.expires_at < now
        ]
        for k in expired_keys:
            del self._pending[k]
        return len(expired_keys)
