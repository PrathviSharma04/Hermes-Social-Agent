"""Telegram message formatting and inline keyboards."""

from typing import Any, Dict, List, Tuple
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def build_approval_card(post: Dict[str, Any], topic: Dict[str, Any]) -> Tuple[str, InlineKeyboardMarkup]:
    """Render the approval card with text and inline keyboard."""
    
    text = (
        "📋 *CONTENT READY*\n\n"
        f"*Topic:* {topic.get('canonical_topic', 'Unknown')}\n"
        f"*Platform:* {post.get('platform', 'unknown').title()}\n"
        f"*Format:* {post.get('format', 'unknown').title()}\n"
        f"*Quality:* {post.get('quality_score', 0):.0f}/100\n"
        f"*Scheduled:* {post.get('scheduled_at', 'Not set')}\n\n"
        f"{post.get('body', '')[:300]}..."
    )
    
    post_id = post["id"]
    keyboard = [
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{post_id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{post_id}")
        ],
        [
            InlineKeyboardButton("📝 REVISE", callback_data=f"revise_{post_id}"),
            InlineKeyboardButton("🗓️ RESCHEDULE", callback_data=f"reschedule_{post_id}")
        ]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def build_confirmation_card(action_description: str, action_id: str) -> Tuple[str, InlineKeyboardMarkup]:
    """Render a confirmation prompt for destructive actions."""
    text = f"⚠️ *CONFIRMATION REQUIRED*\n\nAre you sure you want to:\n{action_description}"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ YES", callback_data=f"confirm_{action_id}"),
            InlineKeyboardButton("❌ NO", callback_data=f"cancel_{action_id}")
        ]
    ]
    
    return text, InlineKeyboardMarkup(keyboard)


def format_status_report(posts: List[Dict], runs: List[Dict]) -> str:
    """Format a concise status report of agent activity."""
    drafts = sum(1 for p in posts if p["status"] == "DRAFT")
    scheduled = sum(1 for p in posts if p["status"] == "SCHEDULED")
    published = sum(1 for p in posts if p["status"] == "PUBLISHED")
    
    report = (
        "📊 *SYSTEM STATUS*\n\n"
        f"📝 Drafts pending: {drafts}\n"
        f"🗓️ Scheduled posts: {scheduled}\n"
        f"✅ Published recently: {published}\n"
    )
    
    if runs:
        report += "\n*Recent Operations:*\n"
        for r in runs[:3]:
            icon = "✅" if r["success"] else "❌"
            report += f"{icon} {r['task_type']} ({r['model_route']})\n"
            
    return report


def format_performance_report(snapshots: List[Dict]) -> str:
    """Format a performance report for recent posts."""
    if not snapshots:
        return "No performance data available yet."
        
    report = "📈 *PERFORMANCE REPORT*\n\n"
    
    for s in snapshots[:5]:
        report += (
            f"Post ID {s['post_id']} ({s['window']}):\n"
            f"👁️ Impressions: {s.get('impressions', 0)}\n"
            f"❤️ Likes: {s.get('likes', 0)}\n"
            f"💬 Comments: {s.get('comments', 0)}\n\n"
        )
        
    return report
