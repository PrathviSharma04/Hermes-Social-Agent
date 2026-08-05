"""Content Council (Critics)."""

import logging
from typing import Any, Dict, List

from hermes_social.generation.models import CriticFeedback, PlatformDraft
from hermes_social.llm.client import execute_prompt
from hermes_social.research.models import KnowledgePack

logger = logging.getLogger(__name__)


def run_content_council(
    conn: Any,
    drafts: List[PlatformDraft],
    knowledge_pack: KnowledgePack,
    model_route: str = "gemini/gemini-1.5-pro"
) -> Dict[str, CriticFeedback]:
    """Execute all critics on the drafts."""
    
    critics = {
        "Research Critic": "Check factual accuracy, source support, misleading simplification, and stale information.",
        "Skeptic": "Ask: what could be wrong? What would a knowledgeable critic challenge? Are we overstating?",
        "Audience Critic": "Ask: why should the target audience care? What do they gain? Is this obvious?",
        "Human-Writing Critic": "Detect AI clichés, repetitive rhythm, generic hook, unnecessary drama, unnatural transitions, fake authority.",
        "Brand Critic": "Check voice, positioning, and brand risk.",
        "Growth Critic": "Check stop-scroll strength, clarity, share/save potential, format choice."
    }
    
    # We will combine all drafts into one payload for the critics to review
    drafts_payload = "\n\n".join(
        f"--- {d.platform.upper()} DRAFT ---\n{d.text_content}\nMEDIA: {d.media_requirements}"
        for d in drafts
    )
    
    results = {}
    
    # For a real high-throughput system, these would be executed in parallel.
    # We'll execute them sequentially here for simplicity or run one big prompt to get all feedback.
    # Running one big prompt is more token-efficient and faster.
    
    system_prompt = """You are the Hermes Social Content Council.
    You will act as 6 different critics evaluating the provided drafts against the Research Pack.
    For each critic, provide a score (0-100), a detailed critique, and a list of critical flags (if any).
    Output JSON exactly matching the requested format: a dictionary where keys are the critic names, 
    and values have 'score', 'critique', and 'critical_flags'.
    """
    
    user_prompt = f"""RESEARCH PACK:
    {knowledge_pack.topic}
    Verified Facts: {knowledge_pack.verified_facts}
    
    DRAFTS:
    {drafts_payload}
    
    CRITIC ROLES:
    """
    for name, desc in critics.items():
        user_prompt += f"- {name}: {desc}\n"
        
    try:
        # In this implementation, the `response_format` for dict is a bit tricky with Pydantic natively 
        # when we want a dynamic dict of models. We'll just ask for JSON and parse the raw dict.
        response = execute_prompt(
            conn,
            prompt=user_prompt,
            system_prompt=system_prompt,
            task_type="content_council",
            model_route=model_route,
        )
        
        # Manually construct the CriticFeedback objects
        for name in critics.keys():
            if name in response:
                results[name] = CriticFeedback(**response[name])
            else:
                results[name] = CriticFeedback(score=50, critique="Critic failed to respond.", critical_flags=[])
    except Exception as e:
        logger.error(f"Content Council execution failed: {e}")
        for name in critics.keys():
            results[name] = CriticFeedback(score=0, critique=f"Execution error: {e}", critical_flags=["CRASH"])
            
    return results
