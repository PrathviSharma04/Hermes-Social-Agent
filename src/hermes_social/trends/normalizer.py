"""Raw candidate normalization."""

from datetime import timezone
import re
from typing import List
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from hermes_social.trends.models import RawCandidate


def normalize_candidates(candidates: List[RawCandidate]) -> List[RawCandidate]:
    """Clean and normalize raw candidates.
    
    - Strip HTML from excerpts
    - Normalize whitespace
    - Normalize URLs (strip tracking params)
    - Ensure published_at is timezone-aware UTC
    """
    normalized = []
    
    for candidate in candidates:
        # 1. Clean excerpt (strip HTML tags, excessive whitespace)
        clean_excerpt = re.sub(r'<[^>]+>', '', candidate.excerpt)
        clean_excerpt = re.sub(r'\s+', ' ', clean_excerpt).strip()
        
        # 2. Clean title
        clean_title = re.sub(r'\s+', ' ', candidate.title).strip()
        
        # 3. Clean URL (strip UTM/tracking params)
        clean_url = _clean_url(candidate.url)
        
        # 4. Ensure published_at is UTC aware
        pub_at = candidate.published_at
        if pub_at and pub_at.tzinfo is None:
            pub_at = pub_at.replace(tzinfo=timezone.utc)
            
        candidate.title = clean_title
        candidate.excerpt = clean_excerpt
        candidate.url = clean_url
        candidate.published_at = pub_at
        
        normalized.append(candidate)
        
    return normalized


def _clean_url(url: str) -> str:
    """Remove common tracking parameters from URL."""
    if not url:
        return ""
        
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        
        # Remove tracking params
        clean_qs = {k: v for k, v in qs.items() if not k.startswith('utm_') and k not in ('ref', 'source')}
        
        # Rebuild URL
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(clean_qs, doseq=True),
            parsed.fragment
        ))
    except Exception:
        return url
