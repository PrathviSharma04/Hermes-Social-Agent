"""Safety and Heuristic Checks for final drafts."""

import re
from typing import List

from hermes_social.generation.models import PlatformDraft


def run_safety_checks(draft: PlatformDraft, past_posts: List[str], banned_phrases: List[str]) -> bool:
    """
    Returns True if the draft is safe, False if it violates hard rules.
    """
    
    content = draft.text_content.lower()
    
    # 1. Banned phrases check
    for phrase in banned_phrases:
        if phrase.lower() in content:
            return False
            
    # 2. Fake personal experience check
    # We ban specific unsupported "I" statements if they imply personal anecdotes
    # (In a real system, this could be more sophisticated with an LLM, but heuristic works for MVP)
    anecdote_pattern = re.compile(r'\b(when i was|my friend|my client|i remember when|in my experience)\b')
    if anecdote_pattern.search(content):
        return False
        
    # 3. Very naive duplicate check against past posts
    # (If the exact string is in any past post, fail)
    for past in past_posts:
        if content == past.lower():
            return False
            
    return True
