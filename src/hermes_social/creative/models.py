"""Data models for creative asset generation (Phase 7)."""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class SlideDesign(BaseModel):
    """Detailed design instructions for a single slide in a carousel."""
    slide_number: int = Field(..., description="1-indexed slide number")
    text_content: str = Field(..., description="The actual text to render on the slide")
    image_prompt: Optional[str] = Field(None, description="Prompt for the background/illustration if needed")
    layout_type: str = Field(..., description="e.g., 'title_only', 'split_vertical', 'full_image'")


class CreativeBrief(BaseModel):
    """Structured design brief representing Section 16 requirements."""
    format: str = Field(..., description="e.g., 'carousel', 'single_image'")
    dimensions: Tuple[int, int] = Field(..., description="(width, height) in pixels")
    design_family: str = Field(..., description="The visual family to use from brand.yaml")
    visual_objective: str = Field(..., description="Goal of the visual (e.g., 'stop scroll', 'explain concept')")
    slides: List[SlideDesign] = Field(..., description="Slide-by-slide instructions")
    brand_elements: List[str] = Field(..., description="Required brand elements (e.g., logo, url)")
