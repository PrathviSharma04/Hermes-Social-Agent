"""Detect contradictions between mapped claims."""

import re
from typing import List

from hermes_social.constants import VerificationStatus
from hermes_social.research.models import ExtractedClaim


def detect_contradictions(claims: List[ExtractedClaim]) -> List[ExtractedClaim]:
    """Detect potential contradictions between extracted claims.
    
    Heuristic approach for the deterministic phase:
    1. Group numerical claims that share common keywords
    2. Check for differing numbers.
    3. Check for negation (not, didn't, won't) in similar claims.
    """
    
    # 1. Identify numerical contradictions
    num_claims = [c for c in claims if c.is_numerical]
    number_pattern = re.compile(r'\b(\d+(?:,\d+)*(?:\.\d+)?%?|\$\d+(?:,\d+)*(?:\.\d+)?(?:[mMbBkK])?)\b')
    
    for i, claim_a in enumerate(num_claims):
        nums_a = set(number_pattern.findall(claim_a.claim_text))
        if not nums_a:
            continue
            
        words_a = set(w for w in claim_a.claim_text.lower().split() if len(w) > 4)
        
        for claim_b in num_claims[i+1:]:
            nums_b = set(number_pattern.findall(claim_b.claim_text))
            if not nums_b:
                continue
                
            words_b = set(w for w in claim_b.claim_text.lower().split() if len(w) > 4)
            
            # If they share significant vocabulary but have different numbers
            intersection = words_a.intersection(words_b)
            if len(intersection) >= 3 and not nums_a.intersection(nums_b):
                note = f"Potential numerical contradiction with another source regarding: {', '.join(intersection)}"
                claim_a.contradiction_notes = note
                claim_a.verification_status = VerificationStatus.DISPUTED.value
                claim_b.contradiction_notes = note
                claim_b.verification_status = VerificationStatus.DISPUTED.value
                
    # 2. Identify negation contradictions
    negation_pattern = re.compile(r'\b(not|never|didn\'t|doesn\'t|won\'t|cannot|can\'t)\b', re.IGNORECASE)
    
    for i, claim_a in enumerate(claims):
        has_neg_a = bool(negation_pattern.search(claim_a.claim_text))
        words_a = set(w for w in claim_a.claim_text.lower().split() if len(w) > 4 and not negation_pattern.match(w))
        
        for claim_b in claims[i+1:]:
            has_neg_b = bool(negation_pattern.search(claim_b.claim_text))
            words_b = set(w for w in claim_b.claim_text.lower().split() if len(w) > 4 and not negation_pattern.match(w))
            
            # If they share vocabulary but one is negated and the other isn't
            if has_neg_a != has_neg_b:
                intersection = words_a.intersection(words_b)
                if len(intersection) >= 2:
                    note = f"Potential negation contradiction regarding: {', '.join(intersection)}"
                    claim_a.contradiction_notes = note
                    claim_a.verification_status = VerificationStatus.DISPUTED.value
                    claim_b.contradiction_notes = note
                    claim_b.verification_status = VerificationStatus.DISPUTED.value

    return claims
