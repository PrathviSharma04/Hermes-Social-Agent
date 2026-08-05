"""Markdown writers for Obsidian vault."""

from typing import Dict, List, Any
from hermes_social.obsidian.models import DecisionEntry

def render_strategy_rules_page(platform: str, rules: List[Dict[str, Any]]) -> str:
    """
    Renders the strategy rules page for a specific platform.
    """
    content = f"---\nplatform: {platform}\ntype: strategy_rules\n---\n\n"
    content += f"# Strategy Rules: {platform.capitalize()}\n\n"
    content += "> [!info] Automatically generated from SQLite database.\n\n"
    
    # Group rules by status
    status_order = ["CONFIRMED", "PROVISIONAL", "TESTING", "HYPOTHESIS", "RETIRED"]
    grouped_rules = {s: [] for s in status_order}
    
    for r in rules:
        status = r.get("status", "HYPOTHESIS")
        if status not in grouped_rules:
            grouped_rules[status] = []
        grouped_rules[status].append(r)
        
    for status in status_order:
        status_rules = grouped_rules[status]
        if not status_rules:
            continue
            
        badge = ""
        if status == "CONFIRMED":
            badge = "✅"
        elif status == "PROVISIONAL":
            badge = "⚠️"
        elif status == "TESTING":
            badge = "🧪"
        elif status == "HYPOTHESIS":
            badge = "💡"
        elif status == "RETIRED":
            badge = "❌"
            
        content += f"## {badge} {status}\n\n"
        
        for rule in status_rules:
            content += f"### Rule {rule['id']}: {rule['rule']}\n"
            content += f"- **Confidence**: {rule.get('confidence', 0.0):.1f}/100\n"
            content += f"- **Sample Size**: {rule.get('sample_size', 0)}\n"
            content += f"- **Last Validated**: {rule.get('last_validated_at', 'Unknown')}\n"
            if rule.get('evidence_summary'):
                content += f"- **Evidence**: {rule['evidence_summary']}\n"
            content += "\n"
            
    return content


def render_experiment_page(experiment: Dict[str, Any], assignments: List[Dict[str, Any]]) -> str:
    """
    Renders an individual experiment page.
    """
    exp_id = experiment.get("id")
    name = experiment.get("name", f"Experiment {exp_id}")
    status = experiment.get("status", "DRAFT")
    
    content = f"---\nexperiment_id: {exp_id}\nstatus: {status}\n---\n\n"
    
    status_emoji = "🧪"
    if status == "COMPLETED":
        status_emoji = "✅"
    elif status == "CANCELLED":
        status_emoji = "❌"
        
    content += f"# {status_emoji} {name}\n\n"
    
    content += "## Overview\n"
    content += f"- **Platform**: {experiment.get('platform', 'Cross-platform')}\n"
    content += f"- **Variable**: {experiment.get('variable')}\n"
    content += f"- **Hypothesis**: {experiment.get('hypothesis')}\n"
    content += f"- **Status**: {status}\n"
    content += f"- **Start Date**: {experiment.get('start_date') or 'Pending'}\n"
    content += f"- **End Date**: {experiment.get('end_date') or 'Pending'}\n\n"
    
    content += "## Variants\n"
    content += f"- **A (Control)**: {experiment.get('variant_a')}\n"
    content += f"- **B (Test)**: {experiment.get('variant_b')}\n\n"
    
    content += "## Results\n"
    content += f"- **Confidence**: {experiment.get('confidence', 0.0):.1f}/100\n"
    content += f"- **Minimum Samples Required**: {experiment.get('minimum_samples')}\n"
    content += f"- **Current Sample Size**: {len(assignments)}\n\n"
    
    if experiment.get('conclusion'):
        content += "### Conclusion\n"
        content += f"{experiment['conclusion']}\n\n"
        
    content += "## Assigned Posts\n"
    if assignments:
        for a in assignments:
            content += f"- Post ID {a.get('post_id')} (Variant {a.get('variant')})\n"
    else:
        content += "*No posts assigned yet.*\n"
        
    return content


def render_monthly_review(year: int, month: int, stats: Dict[str, Any]) -> str:
    """
    Renders the monthly review page.
    """
    month_str = f"{year}-{month:02d}"
    content = f"---\nmonth: {month_str}\ntype: monthly_review\n---\n\n"
    content += f"# Monthly Review: {month_str}\n\n"
    
    content += "## Content Production\n"
    content += f"- **Total Posts Published**: {stats.get('total_published', 0)}\n"
    
    if stats.get("platform_breakdown"):
        for plat, count in stats["platform_breakdown"].items():
            content += f"  - {plat.capitalize()}: {count}\n"
    content += "\n"
    
    content += "## Topic Pipeline\n"
    content += f"- **Discovered**: {stats.get('topics_discovered', 0)}\n"
    content += f"- **Accepted**: {stats.get('topics_accepted', 0)}\n"
    content += f"- **Rejected**: {stats.get('topics_rejected', 0)}\n\n"
    
    content += "## Strategy & Experiments\n"
    content += f"- **Experiments Completed**: {stats.get('experiments_completed', 0)}\n"
    content += f"- **New Rules Confirmed**: {stats.get('rules_confirmed', 0)}\n\n"
    
    return content


def render_decision_log_entry(decision: DecisionEntry) -> str:
    """
    Renders a single entry for the decision log.
    """
    content = f"### {decision.timestamp} - {decision.category}\n"
    content += f"**{decision.description}**\n\n"
    content += f"- **Old**: `{decision.old_value}`\n"
    content += f"- **New**: `{decision.new_value}`\n"
    content += f"- **Reason**: {decision.reason}\n\n"
    return content
