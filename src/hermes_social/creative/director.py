"""Creative Director (LLM)."""

import logging
from typing import Any, Dict

from hermes_social.creative.models import CreativeBrief
from hermes_social.llm.client import execute_prompt

logger = logging.getLogger(__name__)


def generate_creative_brief(
    conn: Any,
    post_content: str,
    platform: str,
    brand_context: Dict,
    model_route: str = "gemini/gemini-1.5-pro"
) -> CreativeBrief:
    """Translates post text into a structured slide-by-slide visual brief."""
    
    # Simple logic for format/dimensions based on platform
    dimensions = (1080, 1080)
    format_type = "single_image"
    
    if platform == "instagram":
        dimensions = (1080, 1350)
        format_type = "carousel"
    elif platform == "linkedin":
        dimensions = (1080, 1350) # PDF carousel
        format_type = "carousel"
        
    system_prompt = f"""You are the Hermes Creative Director. 
    Your task is to take the provided draft post text and structure a highly-visual design brief for a designer.
    
    BRAND RULES:
    Visual Families: {', '.join(brand_context.get('visual_families', ['Editorial Explainer']))}
    
    INSTRUCTIONS:
    - Determine how many slides/images this requires. Break down the text logically.
    - DO NOT instruct the AI to generate typography. Text will be overlaid separately.
    - Provide an `image_prompt` only for slides that need an abstract background or illustration.
    - Return the exact JSON structure requested.
    """
    
    user_prompt = f"""PLATFORM: {platform}
    FORMAT TARGET: {format_type}
    DIMENSIONS: {dimensions}
    
    POST CONTENT:
    {post_content}
    """
    
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="creative_brief",
        model_route=model_route,
        response_format=CreativeBrief
    )
    
    # Force dimensions and format as LLM might mess it up
    response["dimensions"] = dimensions
    response["format"] = format_type
    
    return CreativeBrief(**response)
