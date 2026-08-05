"""Writes KnowledgePacks to the Obsidian vault as Markdown.

DEPRECATION NOTICE: This module is deprecated in favor of `hermes_social.obsidian`.
Future vault integrations (Phase 9) should use the new module. This file remains
for backward compatibility during Phase 5 execution.
"""

import re
from pathlib import Path

from hermes_social.research.models import KnowledgePack


def write_knowledge_pack_to_vault(pack: KnowledgePack, vault_path: Path) -> Path:
    """Write a knowledge pack to data/vault/01-Research/{topic_slug}.md"""
    
    # Ensure directory exists
    research_dir = vault_path / "01-Research"
    research_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a safe slug
    slug = re.sub(r'[^a-z0-9]+', '-', pack.topic.lower()).strip('-')
    if not slug:
        slug = f"research-run-{pack.research_run_id}"
        
    filename = f"{slug}.md"
    filepath = research_dir / filename
    
    content = f"""# {pack.topic}

**Overall Confidence:** {pack.overall_confidence:.1f}/100
**Research Run ID:** {pack.research_run_id}

## WHY NOW
{pack.why_now}

## AUDIENCE RELEVANCE
{pack.audience_relevance}

## VERIFIED FACTS
"""
    for fact in pack.verified_facts:
        content += f"- {fact}\n"
        
    content += "\n## IMPORTANT NUMBERS\n"
    for num in pack.important_numbers:
        content += f"- {num}\n"
        
    content += "\n## CONTEXT\n"
    content += f"{pack.context}\n"
    
    content += "\n## WHAT PEOPLE ARE GETTING WRONG\n"
    for w in pack.what_people_get_wrong:
        content += f"- {w}\n"
        
    content += "\n## OPPOSING VIEW\n"
    for v in pack.opposing_views:
        content += f"- {v}\n"
        
    content += "\n## UNCERTAINTIES\n"
    for u in pack.uncertainties:
        content += f"- {u}\n"
        
    content += "\n## POTENTIAL ANGLES\n"
    for a in pack.potential_angles:
        content += f"- {a}\n"
        
    content += "\n## SOURCE MAP\n"
    for s in pack.source_map:
        status_icon = "✅" if s['status'] == 'ok' else "❌"
        content += f"- {status_icon} [{s['title']}]({s['url']}) (Authority: {s['authority']}, Claims: {s['claims_count']})\n"
        
    with filepath.open("w", encoding="utf-8") as f:
        f.write(content)
        
    return filepath
