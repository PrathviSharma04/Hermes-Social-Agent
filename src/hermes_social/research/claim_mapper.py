"""Map claims to sources and consolidate duplicates."""

from difflib import SequenceMatcher
from typing import List

from hermes_social.constants import VerificationStatus
from hermes_social.research.models import ExtractedClaim, FetchedSource


def map_claims_to_sources(
    claims: List[ExtractedClaim],
    sources: List[FetchedSource]
) -> List[ExtractedClaim]:
    """Consolidate similar claims and map them to their sources.
    Boosts confidence for claims supported by multiple independent sources.
    """
    consolidated: List[ExtractedClaim] = []
    
    # We use a fuzzy match to group similar claims across sources
    for claim in claims:
        # Check if we already have this claim
        found_match = False
        for existing in consolidated:
            ratio = SequenceMatcher(None, claim.claim_text.lower(), existing.claim_text.lower()).ratio()
            if ratio > 0.60:
                # Merge sources
                for url, sid in zip(claim.source_urls, claim.source_ids):
                    if url not in existing.source_urls:
                        existing.source_urls.append(url)
                    if sid not in existing.source_ids:
                        existing.source_ids.append(sid)
                found_match = True
                break
                
        if not found_match:
            consolidated.append(claim)

    # Now update confidence and verification status based on source count
    for claim in consolidated:
        source_count = len(claim.source_urls)
        
        if source_count == 0:
            claim.confidence = 0.0
            claim.verification_status = VerificationStatus.UNVERIFIED.value
        elif source_count == 1:
            claim.confidence = 60.0
            claim.verification_status = VerificationStatus.VERIFIED.value
        elif source_count == 2:
            claim.confidence = 85.0
            claim.verification_status = VerificationStatus.VERIFIED.value
        else:
            claim.confidence = 95.0
            claim.verification_status = VerificationStatus.VERIFIED.value
            
    return consolidated
