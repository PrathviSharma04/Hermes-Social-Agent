"""Tests for the Telegram Command Center (Phase 10)."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from hermes_social.constants import TelegramIntent
from hermes_social.telegram.intents import TelegramIntentParser, ParsedIntent
from hermes_social.telegram.confirmation import ConfirmationManager
from hermes_social.telegram.cards import build_approval_card, format_status_report


def test_intent_parser_keyword_fallback():
    parser = TelegramIntentParser()
    
    # Test keyword fast-paths
    parsed = parser.parse("Stop everything", Mock())
    assert parsed.intent == TelegramIntent.EMERGENCY_STOP
    
    parsed = parser.parse("pause publishing", Mock())
    assert parsed.intent == TelegramIntent.PAUSE_PUBLISHING


@patch("hermes_social.telegram.intents.execute_prompt")
def test_intent_parser_llm(mock_execute_prompt):
    parser = TelegramIntentParser()
    
    mock_execute_prompt.return_value = {
        "intent": "CREATE_POST",
        "confidence": 0.95,
        "parameters": {"topic": "AI Agents"}
    }
    
    parsed = parser.parse("Create a carousel about AI agents", Mock())
    assert parsed.intent == TelegramIntent.CREATE_POST
    assert parsed.confidence == 0.95
    assert parsed.parameters["topic"] == "AI Agents"


def test_confirmation_manager():
    manager = ConfirmationManager(expiry_minutes=15)
    
    assert manager.requires_confirmation(TelegramIntent.EMERGENCY_STOP) is True
    assert manager.requires_confirmation(TelegramIntent.QUERY_STATUS) is False
    
    parsed_intent = ParsedIntent(TelegramIntent.EMERGENCY_STOP, 1.0, "stop")
    pending = manager.create_pending(parsed_intent)
    
    assert pending.action_id is not None
    
    # Confirm it
    confirmed = manager.confirm(pending.action_id)
    assert confirmed is not None
    assert confirmed.intent == TelegramIntent.EMERGENCY_STOP
    
    # Confirming again should return None (already processed)
    assert manager.confirm(pending.action_id) is None


def test_build_approval_card():
    post = {
        "id": 42,
        "platform": "linkedin",
        "format": "carousel",
        "quality_score": 95,
        "scheduled_at": "2026-08-10 10:00:00",
        "body": "This is a great post."
    }
    topic = {"canonical_topic": "AI Trends"}
    
    text, keyboard = build_approval_card(post, topic)
    
    assert "AI Trends" in text
    assert "Linkedin" in text
    assert "95/100" in text
    assert "This is a great post." in text
    
    # Check callback data
    assert keyboard.inline_keyboard[0][0].callback_data == "approve_42"


def test_format_status_report():
    posts = [
        {"status": "DRAFT"},
        {"status": "DRAFT"},
        {"status": "SCHEDULED"},
        {"status": "PUBLISHED"}
    ]
    runs = [
        {"task_type": "research", "model_route": "gpt-4", "success": True},
        {"task_type": "generation", "model_route": "gpt-4", "success": False}
    ]
    
    report = format_status_report(posts, runs)
    
    assert "Drafts pending: 2" in report
    assert "Scheduled posts: 1" in report
    assert "Published recently: 1" in report
    assert "✅ research" in report
    assert "❌ generation" in report
