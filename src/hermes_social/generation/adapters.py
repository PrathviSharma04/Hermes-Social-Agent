"""Platform Adapters (Section 12)."""

import logging
from typing import Any, Dict

from hermes_social.generation.models import MasterNarrative, PlatformDraft
from hermes_social.llm.client import execute_prompt

logger = logging.getLogger(__name__)


def adapt_for_linkedin(
    conn: Any,
    narrative: MasterNarrative,
    brand_context: Dict,
    model_route: str = "gemini/gemini-1.5-pro"
) -> PlatformDraft:
    """Optimize for professional insight and readable formatting."""
    
    system_prompt = f"""You are a master LinkedIn copywriter. Adapt the provided Master Narrative for LinkedIn.
    Optimize for: professional relevance, clear narrative, useful insight, and readable formatting (short paragraphs).
    Brand Voice: {brand_context.get('brand_voice', 'Professional')}
    """
    
    user_prompt = f"MASTER NARRATIVE:\n{narrative.model_dump_json(indent=2)}"
    
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="adapter_linkedin",
        model_route=model_route,
        response_format=PlatformDraft
    )
    
    return PlatformDraft(**response)


def adapt_for_x(
    conn: Any,
    narrative: MasterNarrative,
    brand_context: Dict,
    model_route: str = "gemini/gemini-1.5-pro"
) -> PlatformDraft:
    """Optimize for compressed clarity."""
    
    system_prompt = f"""You are a master Twitter/X copywriter. Adapt the provided Master Narrative for X.
    Optimize for: compressed clarity, sharp hook, conversational language. No unnecessary LinkedIn-style formatting.
    Brand Voice: {brand_context.get('brand_voice', 'Professional')}
    """
    
    user_prompt = f"MASTER NARRATIVE:\n{narrative.model_dump_json(indent=2)}"
    
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="adapter_x",
        model_route=model_route,
        response_format=PlatformDraft
    )
    
    return PlatformDraft(**response)


def adapt_for_instagram(
    conn: Any,
    narrative: MasterNarrative,
    brand_context: Dict,
    model_route: str = "gemini/gemini-1.5-pro"
) -> PlatformDraft:
    """Optimize for visual storytelling."""
    
    system_prompt = f"""You are a master Instagram copywriter and visual strategist. Adapt the provided Master Narrative for Instagram.
    Optimize for: visual storytelling, strong first slide, carousel progression, and a concise caption.
    Output the carousel script in `text_content` and visual instructions in `media_requirements`.
    Brand Voice: {brand_context.get('brand_voice', 'Professional')}
    """
    
    user_prompt = f"MASTER NARRATIVE:\n{narrative.model_dump_json(indent=2)}"
    
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="adapter_instagram",
        model_route=model_route,
        response_format=PlatformDraft
    )
    
    return PlatformDraft(**response)
