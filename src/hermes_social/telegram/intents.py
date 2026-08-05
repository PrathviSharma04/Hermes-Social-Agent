"""Telegram Natural Language Intent Parser."""

import logging
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from hermes_social.constants import TelegramIntent
from hermes_social.llm.client import execute_prompt

logger = logging.getLogger(__name__)


@dataclass
class ParsedIntent:
    """Represents a parsed user intent from natural language."""
    intent: TelegramIntent
    confidence: float
    raw_text: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class TelegramIntentParser:
    """Parses natural language into structured TelegramIntents."""
    
    SYSTEM_PROMPT = """You are the intent parser for Hermes Social Agent.
Your job is to map natural language commands to one of the predefined intents.

Intents available:
- QUERY_STATUS: Ask about current operations (e.g. "What are you posting tomorrow?")
- QUERY_PERFORMANCE: Ask about metrics (e.g. "Show me this week's performance", "Why did yesterday underperform?")
- QUERY_LEARNINGS: Ask about strategy rules (e.g. "What have you learned this month?")
- QUERY_RESEARCH: Ask about research (e.g. "Show me today's research")
- CREATE_TOPIC: Suggest a new topic
- CREATE_POST: Request a new post (e.g. "Create a carousel about AI agents")
- SCHEDULE_POST: Schedule an existing post
- RESCHEDULE_POST: Change post time (e.g. "Post this on LinkedIn next Friday at 10 AM")
- CANCEL_POST: Cancel a post (e.g. "Cancel the August 12 post", "Do not post tomorrow")
- PAUSE_PLATFORM: Pause a specific platform (e.g. "Pause Instagram for one week")
- RESUME_PLATFORM: Resume a specific platform
- PAUSE_PUBLISHING: Pause all publishing
- RESUME_PUBLISHING: Resume all publishing
- PAUSE_AUTOPILOT: Disable autopilot
- RESUME_AUTOPILOT: Enable autopilot
- APPROVE_POST: Approve a post (e.g. "Approve tomorrow's post")
- REJECT_POST: Reject an idea or post (e.g. "Reject this idea")
- REVISE_POST: Rewrite text (e.g. "Rewrite only slide 1")
- REVISE_ASSET: Change visual design (e.g. "Make the design more minimal")
- CHANGE_FORMAT: Change post format (e.g. "Switch tomorrow to a single-image post")
- FORCE_RESEARCH: Force deep research
- FORCE_ANALYSIS: Force analysis
- EMERGENCY_STOP: Halts the entire agent (publishing, research, generation). e.g. "Stop everything", "Halt"

If you cannot confidently classify the command, use UNKNOWN.

Output valid JSON ONLY with this structure:
{
    "intent": "<INTENT_NAME>",
    "confidence": 0.95,
    "parameters": {
        "platform": "linkedin/instagram/x (if mentioned)",
        "target_date": "next friday (if mentioned)",
        "topic": "extracted topic (if mentioned)"
    }
}
"""

    def parse(self, raw_text: str, conn: sqlite3.Connection) -> ParsedIntent:
        """Parse raw text into an intent. Uses LLM with a keyword fallback."""
        text_lower = raw_text.lower().strip()
        
        # Fast-path / Keyword fallback for critical commands or when LLM fails
        if text_lower in ("stop everything", "halt", "emergency stop"):
            return ParsedIntent(TelegramIntent.EMERGENCY_STOP, 1.0, raw_text)
        if text_lower in ("stop publishing", "pause publishing"):
            return ParsedIntent(TelegramIntent.PAUSE_PUBLISHING, 1.0, raw_text)
        if text_lower in ("resume publishing", "start publishing"):
            return ParsedIntent(TelegramIntent.RESUME_PUBLISHING, 1.0, raw_text)
            
        try:
            # We use gemini-1.5-flash since this is a fast classification task
            response = execute_prompt(
                conn=conn,
                prompt=f"User command: '{raw_text}'\nParse this intent.",
                system_prompt=self.SYSTEM_PROMPT,
                task_type="telegram_intent_parsing",
                model_route="gemini/gemini-1.5-flash",
                response_format=dict
            )
            
            intent_str = response.get("intent", "UNKNOWN")
            try:
                intent = TelegramIntent(intent_str)
            except ValueError:
                intent = TelegramIntent.UNKNOWN
                
            confidence = float(response.get("confidence", 0.0))
            parameters = response.get("parameters", {})
            
            return ParsedIntent(
                intent=intent,
                confidence=confidence,
                raw_text=raw_text,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"Failed to parse intent via LLM: {e}")
            
            # Very basic fallback matching
            if "approve" in text_lower:
                return ParsedIntent(TelegramIntent.APPROVE_POST, 0.5, raw_text)
            elif "reject" in text_lower:
                return ParsedIntent(TelegramIntent.REJECT_POST, 0.5, raw_text)
            elif "pause" in text_lower:
                return ParsedIntent(TelegramIntent.PAUSE_PLATFORM, 0.5, raw_text)
                
            return ParsedIntent(TelegramIntent.UNKNOWN, 0.0, raw_text)
