"""Editor-in-Chief Orchestration."""

import logging
from typing import Any, Dict

from hermes_social.generation.models import CriticFeedback, EditorDecision
from hermes_social.llm.client import execute_prompt

logger = logging.getLogger(__name__)


def evaluate_drafts(
    conn: Any,
    council_feedback: Dict[str, CriticFeedback],
    model_route: str = "gemini/gemini-1.5-pro"
) -> EditorDecision:
    """Decides if the drafts meet the Phase 6 quality gate thresholds."""
    
    # We can use LLM to synthesize the decision, but we can also use deterministic gates
    # Section 15 Quality Gate thresholds:
    # Writing quality >= 85, Brand fit >= 90
    
    writing_score = council_feedback.get("Human-Writing Critic", CriticFeedback(score=0, critique="", critical_flags=[])).score
    brand_score = council_feedback.get("Brand Critic", CriticFeedback(score=0, critique="", critical_flags=[])).score
    research_score = council_feedback.get("Research Critic", CriticFeedback(score=0, critique="", critical_flags=[])).score
    
    # Calculate average
    scores = {name: fb.score for name, fb in council_feedback.items()}
    avg_score = sum(scores.values()) / len(scores) if scores else 0
    
    # Check for hard flags
    all_flags = []
    for fb in council_feedback.values():
        all_flags.extend(fb.critical_flags)
        
    system_prompt = """You are the Editor-in-Chief. You synthesize the Content Council's feedback.
    You must output a decision of PASS, REVISE, or REJECT, along with revision_notes.
    If there are critical flags or scores are low, you MUST REVISE or REJECT.
    """
    
    user_prompt = f"""COUNCIL FEEDBACK:
    """
    for name, fb in council_feedback.items():
        user_prompt += f"- {name} (Score: {fb.score}): {fb.critique}\n  Flags: {fb.critical_flags}\n"
        
    response = execute_prompt(
        conn,
        prompt=user_prompt,
        system_prompt=system_prompt,
        task_type="editor_in_chief",
        model_route=model_route,
        response_format=EditorDecision
    )
    
    decision = EditorDecision(**response)
    
    # Deterministic overrides to enforce Section 15 gates
    if writing_score < 85 or brand_score < 90 or research_score < 90:
        if decision.decision == "PASS":
            decision.decision = "REVISE"
            decision.revision_notes = (decision.revision_notes or "") + "\nAUTOMATED GATE: Failed minimum score thresholds."
            
    if all_flags:
        if decision.decision == "PASS":
            decision.decision = "REVISE"
            decision.revision_notes = (decision.revision_notes or "") + "\nAUTOMATED GATE: Must address critical flags."
            
    # Force the scores into the final dict
    decision.final_scores = scores
    
    return decision
