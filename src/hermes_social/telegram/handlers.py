"""Action handlers for Telegram intents."""

import logging
import sqlite3
from typing import Dict, Any, Tuple

from hermes_social.config import AppConfig
from hermes_social.constants import TelegramIntent, PostStatus
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.db.repositories.operations import OperationsRepository
from hermes_social.telegram.intents import ParsedIntent
from hermes_social.telegram.cards import format_status_report, format_performance_report
from hermes_social.db.repositories.performance import PerformanceRepository
from hermes_social.metrics.analyzer import evaluate_post
import logging

logger = logging.getLogger(__name__)


def handle_intent(
    parsed_intent: ParsedIntent, 
    conn: sqlite3.Connection, 
    config: AppConfig
) -> str:
    """Route a parsed intent to the appropriate handler logic."""
    intent = parsed_intent.intent
    params = parsed_intent.parameters
    
    if intent == TelegramIntent.QUERY_STATUS:
        return _handle_query_status(conn)
    elif intent == TelegramIntent.QUERY_PERFORMANCE:
        return _handle_query_performance(conn)
    elif intent == TelegramIntent.APPROVE_POST:
        return _handle_approve_post(conn, params)
    elif intent == TelegramIntent.REJECT_POST:
        return _handle_reject_post(conn, params)
    elif intent == TelegramIntent.PAUSE_PUBLISHING:
        return _handle_pause_publishing(conn, config)
    elif intent == TelegramIntent.RESUME_PUBLISHING:
        return _handle_resume_publishing(conn, config)
    elif intent == TelegramIntent.EMERGENCY_STOP:
        return _handle_emergency_stop(conn, config)
    elif intent == TelegramIntent.UNKNOWN:
        return "I'm not sure how to handle that command. Try asking about status, approving a post, or pausing publishing."
        
    return f"Acknowledged: {intent.value}. (Handler not fully implemented for this intent yet)"


def _handle_query_status(conn: sqlite3.Connection) -> str:
    """Handle QUERY_STATUS intent."""
    post_repo = PostRepository(conn)
    ops_repo = OperationsRepository(conn)
    
    recent_posts = post_repo.get_recent_posts(days=7)
    recent_runs = []
    
    cursor = conn.execute("SELECT * FROM model_runs ORDER BY id DESC LIMIT 5")
    recent_runs = [dict(row) for row in cursor.fetchall()]
    
    return format_status_report(recent_posts, recent_runs)


def _handle_query_performance(conn: sqlite3.Connection) -> str:
    """Handle QUERY_PERFORMANCE intent."""
    post_repo = PostRepository(conn)
    perf_repo = PerformanceRepository(conn)
    
    # Get last 5 published posts
    recent_published = post_repo.list_by_status(PostStatus.PUBLISHED)[:5]
    
    if not recent_published:
        return "No published posts found to report performance on."
        
    posts_data = []
    for post in recent_published:
        snapshots = perf_repo.list_by_post(post["id"])
        _, score_str = evaluate_post(post["id"], conn)
        
        posts_data.append({
            "post": post,
            "snapshots": snapshots,
            "baseline_score": score_str
        })
        
    return format_performance_report(posts_data)


def _handle_approve_post(conn: sqlite3.Connection, params: Dict[str, Any]) -> str:
    """Handle APPROVE_POST intent."""
    post_repo = PostRepository(conn)
    
    # In a real scenario, params might contain the post ID if they said "approve post 5".
    # Otherwise, we approve the most recent READY_FOR_APPROVAL post.
    post_id = params.get("post_id")
    
    if not post_id:
        # Find latest pending
        pending = post_repo.list_by_status(PostStatus.READY_FOR_APPROVAL)
        if not pending:
            return "There are no posts waiting for approval right now."
        post_id = pending[0]["id"]
        
    try:
        post_repo.update_status(int(post_id), PostStatus.APPROVED)
        return f"✅ Post {post_id} has been approved."
    except Exception as e:
        logger.error(f"Failed to approve post {post_id}: {e}")
        return f"Failed to approve post: {e}"


def _handle_reject_post(conn: sqlite3.Connection, params: Dict[str, Any]) -> str:
    """Handle REJECT_POST intent."""
    post_repo = PostRepository(conn)
    post_id = params.get("post_id")
    
    if not post_id:
        pending = post_repo.list_by_status(PostStatus.READY_FOR_APPROVAL)
        if not pending:
            return "There are no posts waiting for approval right now."
        post_id = pending[0]["id"]
        
    try:
        post_repo.update_status(int(post_id), PostStatus.REJECTED)
        return f"❌ Post {post_id} has been rejected."
    except Exception as e:
        return f"Failed to reject post: {e}"


def _handle_pause_publishing(conn: sqlite3.Connection, config: AppConfig) -> str:
    """Handle PAUSE_PUBLISHING intent."""
    ops_repo = OperationsRepository(conn)
    # Ideally we update the runtime DB config, but for now log it and mock the change
    config.publishing_enabled = False
    ops_repo.log_system_event(
        level="WARNING",
        category="CONTROL",
        message="Publishing paused via Telegram."
    )
    conn.commit()
    return "⏸️ Publishing has been paused. I will continue research and generation, but nothing will be posted."


def _handle_resume_publishing(conn: sqlite3.Connection, config: AppConfig) -> str:
    """Handle RESUME_PUBLISHING intent."""
    ops_repo = OperationsRepository(conn)
    config.publishing_enabled = True
    ops_repo.log_system_event(
        level="INFO",
        category="CONTROL",
        message="Publishing resumed via Telegram."
    )
    conn.commit()
    return "▶️ Publishing has been resumed."


def _handle_emergency_stop(conn: sqlite3.Connection, config: AppConfig) -> str:
    """Handle EMERGENCY_STOP intent."""
    ops_repo = OperationsRepository(conn)
    config.publishing_enabled = False
    config.autopilot_enabled = False
    
    ops_repo.log_system_event(
        level="CRITICAL",
        category="CONTROL",
        message="EMERGENCY STOP activated via Telegram."
    )
    conn.commit()
    return "🛑 *EMERGENCY STOP ACTIVATED*\nAll publishing and autopilot features have been halted."
