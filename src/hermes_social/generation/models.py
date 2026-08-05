"""Data models for content generation (Phase 6)."""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class MasterNarrative(BaseModel):
    """Platform-agnostic master narrative structure (Section 11)."""
    hook: str = Field(..., description="The attention-grabbing opening idea")
    core_thesis: str = Field(..., description="The main argument or statement")
    why_it_matters: str = Field(..., description="Why the audience should care right now")
    evidence: List[str] = Field(..., description="Supporting facts and data points")
    insight: str = Field(..., description="The non-obvious takeaway or realization")
    practical_takeaway: str = Field(..., description="What the reader should do differently")
    optional_cta: Optional[str] = Field(None, description="Optional call to action")


class PlatformDraft(BaseModel):
    """A draft adapted for a specific platform."""
    platform: str = Field(..., description="linkedin, x, or instagram")
    text_content: str = Field(..., description="The full text content/caption/thread")
    format_type: str = Field(..., description="text, thread, carousel_script, etc.")
    media_requirements: Optional[str] = Field(None, description="Instructions for visuals if any")


class CriticFeedback(BaseModel):
    """Feedback from a single member of the Content Council."""
    score: int = Field(..., description="Score from 0 to 100")
    critique: str = Field(..., description="Detailed feedback on the draft")
    critical_flags: List[str] = Field(default_factory=list, description="Any hard violations found")


class EditorDecision(BaseModel):
    """Final decision from the Editor-in-Chief."""
    decision: str = Field(..., description="PASS, REVISE, or REJECT")
    revision_notes: Optional[str] = Field(None, description="Instructions for the next revision if REVISE")
    final_scores: Dict[str, int] = Field(..., description="Dictionary of final scores (writing, brand, relevance, etc.)")
