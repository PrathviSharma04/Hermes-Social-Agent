"""Master Narrative Generator."""

import logging
from typing import Any, Dict, Optional

from hermes_social.generation.models import MasterNarrative
from hermes_social.llm.client import execute_prompt
from hermes_social.research.models import KnowledgePack

logger = logging.getLogger(__name__)


def generate_master_narrative(
    conn: Any,
    knowledge_pack: KnowledgePack,
    brand_context: Dict,
    model_route: str = "gemini/gemini-1.5-pro",
    previous_feedback: Optional[str] = None
) -> MasterNarrative:
    """Uses LLM to synthesize research into the Section 11 master narrative structure."""
    
    system_prompt = f"""You are an elite Content Strategist. Your job is to take raw research and distill it into a powerful, platform-agnostic 'Master Narrative'.
    
    BRAND RULES:
    Voice: {brand_context.get('brand_voice', 'Professional and insightful')}
    Pillars: {', '.join(brand_context.get('content_pillars', []))}
    
    CRITICAL CONSTRAINT: Do NOT invent facts. Only use the facts provided in the Research Pack.
    """
    
    user_prompt = f"""RESEARCH PACK:
    Topic: {knowledge_pack.topic}
    Why Now: {knowledge_pack.why_now}
    Verified Facts:
    {chr(10).join(f'- {f}' for f in knowledge_pack.verified_facts)}
    Important Numbers:
    {chr(10).join(f'- {n}' for n in knowledge_pack.important_numbers)}
    What People Get Wrong:
    {chr(10).join(f'- {w}' for w in knowledge_pack.what_people_get_wrong)}
    """
    
    if previous_feedback:
        user_prompt += f"\n\nPREVIOUS FEEDBACK TO ADDRESS:\n{previous_feedback}"
        
    user_prompt += """
    
    Generate the Master Narrative. Ensure it fits the JSON schema exactly.
    """
    
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="master_narrative",
        model_route=model_route,
        response_format=MasterNarrative
    )
    
    return MasterNarrative(**response)
