"""Deduplication logic for trend candidates."""

from difflib import SequenceMatcher
from typing import Dict, List

from hermes_social.trends.models import RawCandidate


def deduplicate_candidates(
    candidates: List[RawCandidate],
    existing_topics: List[Dict],
    similarity_threshold: float = 0.85,
) -> List[RawCandidate]:
    """Remove duplicate candidates using:
    1. Exact URL match within batch or against DB.
    2. Title similarity using SequenceMatcher.
    """
    unique_candidates = []
    
    # 1. Build sets of existing URLs and Titles from DB topics (assuming topic_sources are joined/known or URLs are stored)
    # Since existing_topics doesn't have URL directly in `topics` table, we primarily dedup against titles here.
    # If the caller provides source URLs in `existing_topics`, we use them.
    existing_urls = set()
    existing_titles = set(t.get("canonical_topic", "").lower() for t in existing_topics)
    
    for t in existing_topics:
        # Assuming caller might enrich existing_topics with a 'sources' list containing URLs
        for src in t.get("sources", []):
            if src.get("url"):
                existing_urls.add(src["url"])

    # Local sets for intra-batch dedup
    seen_urls = set(existing_urls)
    seen_titles = []  # keep list for fuzzy matching intra-batch
    
    for candidate in candidates:
        # Check 1: Exact URL match
        if candidate.url and candidate.url in seen_urls:
            continue
            
        # Check 2: Exact Title match (lower)
        lower_title = candidate.title.lower()
        if lower_title in existing_titles:
            continue
            
        # Check 3: Fuzzy Title match intra-batch
        is_fuzzy_duplicate = False
        for seen_title in seen_titles:
            ratio = SequenceMatcher(None, lower_title, seen_title).ratio()
            if ratio >= similarity_threshold:
                is_fuzzy_duplicate = True
                break
                
        # Check 4: Fuzzy Title match DB topics (only check if not already a dup)
        if not is_fuzzy_duplicate:
            for db_title in existing_titles:
                ratio = SequenceMatcher(None, lower_title, db_title).ratio()
                if ratio >= similarity_threshold:
                    is_fuzzy_duplicate = True
                    break

        if not is_fuzzy_duplicate:
            unique_candidates.append(candidate)
            if candidate.url:
                seen_urls.add(candidate.url)
            seen_titles.append(lower_title)
            
    return unique_candidates
