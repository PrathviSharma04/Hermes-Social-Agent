"""Extract and classify claims from source text."""

import re
from typing import List

from hermes_social.constants import ClaimType
from hermes_social.research.models import ExtractedClaim, FetchedSource


def extract_claims(sources: List[FetchedSource]) -> List[ExtractedClaim]:
    """Extract claims from fetched sources using heuristic patterns."""
    all_claims = []
    
    # Very basic sentence splitting (not perfect, but works for heuristics)
    sentence_pattern = re.compile(r'([^.!?]+[.!?]+)')
    
    # Patterns
    number_pattern = re.compile(r'\b(\d+(?:,\d+)*(?:\.\d+)?%?|\$\d+(?:,\d+)*(?:\.\d+)?(?:[mMbBkK])?)\b')
    opinion_pattern = re.compile(r'\b(i think|in my opinion|arguably|should|it seems|believe|feel)\b', re.IGNORECASE)
    prediction_pattern = re.compile(r'\b(will|is expected to|could|might|predicted|projected|future)\b', re.IGNORECASE)
    
    for source in sources:
        if source.fetch_status != "ok" or not source.text_content:
            continue
            
        sentences = sentence_pattern.findall(source.text_content)
        extracted_for_source = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 30 or len(sentence) > 300:
                continue
                
            # Classify
            is_num = bool(number_pattern.search(sentence))
            is_opinion = bool(opinion_pattern.search(sentence))
            is_prediction = bool(prediction_pattern.search(sentence))
            
            # Determine claim type
            # Order of precedence: PERSONAL_EXPERIENCE (handled elsewhere/manual), OPINION, PREDICTION, FACT
            if is_opinion:
                c_type = ClaimType.OPINION.value
            elif is_prediction:
                c_type = ClaimType.PREDICTION.value
            else:
                c_type = ClaimType.FACT.value
                
            # Filtering: Not every sentence is a claim. 
            # We only extract if it has numbers OR is an opinion/prediction OR is a strong assertion.
            # For this heuristic, we'll take all that have numbers, opinions, predictions, 
            # or contain assertive verbs like (is, are, has, increases, decreases, shows).
            strong_assertion = re.search(r'\b(is|are|has|increases|decreases|shows|proves|found)\b', sentence, re.IGNORECASE)
            
            if is_num or is_opinion or is_prediction or strong_assertion:
                # To prevent duplicates across sources within this function, we just emit everything.
                # The mapper will deduplicate later.
                claim = ExtractedClaim(
                    claim_text=sentence,
                    claim_type=c_type,
                    source_urls=[source.url],
                    source_ids=[source.source_id],
                    confidence=50.0,  # Base confidence for 1 source
                    is_numerical=is_num,
                    verification_status="UNVERIFIED",  # Base status until mapped
                    contradiction_notes=None
                )
                all_claims.append(claim)
                extracted_for_source += 1
                
            if extracted_for_source >= 20:
                break
                
    return all_claims
