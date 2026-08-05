"""Compute overall research confidence."""

from typing import List

from hermes_social.constants import VerificationStatus
from hermes_social.research.models import ExtractedClaim, FetchedSource


def compute_research_confidence(
    claims: List[ExtractedClaim],
    sources: List[FetchedSource]
) -> float:
    """Compute overall research confidence score (0-100).
    
    Factors:
    - Percentage of claims with >=1 source
    - Presence of multi-source verified claims
    - Absence of unresolved contradictions
    - Base authority of the sources used
    """
    
    if not claims or not sources:
        return 0.0
        
    # 1. Source Authority Base (max 40 points)
    # Average authority of successfully fetched sources
    ok_sources = [s for s in sources if s.fetch_status == "ok"]
    if not ok_sources:
        return 0.0
        
    avg_authority = sum(s.authority_score for s in ok_sources) / len(ok_sources)
    authority_score = (avg_authority / 100.0) * 40.0
    
    # 2. Claim Verification Rate (max 40 points)
    verified_claims = [c for c in claims if c.verification_status == VerificationStatus.VERIFIED.value]
    verification_ratio = len(verified_claims) / len(claims)
    verification_score = verification_ratio * 40.0
    
    # 3. Multi-source Corroboration Bonus (max 10 points)
    multi_source_claims = [c for c in verified_claims if len(c.source_urls) > 1]
    corroboration_ratio = len(multi_source_claims) / len(claims)
    corroboration_score = min(10.0, corroboration_ratio * 20.0)
    
    # 4. Contradiction Penalty (-10 per disputed claim, up to -20)
    disputed_claims = [c for c in claims if c.verification_status == VerificationStatus.DISPUTED.value]
    contradiction_penalty = min(20.0, len(disputed_claims) * 10.0)
    
    # 5. Numerical Evidence Bonus (max 10 points)
    num_claims = [c for c in verified_claims if c.is_numerical]
    num_ratio = len(num_claims) / len(claims) if claims else 0
    num_score = min(10.0, num_ratio * 20.0)
    
    total = authority_score + verification_score + corroboration_score + num_score - contradiction_penalty
    
    return max(0.0, min(100.0, total))
