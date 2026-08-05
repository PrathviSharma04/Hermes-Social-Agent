"""Freshness scoring and filtering."""

from datetime import datetime, timezone
import math
from typing import List, Optional

from hermes_social.trends.models import RawCandidate


def compute_freshness(published_at: Optional[datetime], max_age_hours: int = 72) -> float:
    """Compute a 0-100 freshness score. Items older than max_age_hours score 0.
    The score decays exponentially with age.
    """
    if not published_at:
        # If no publish date, assume it's fresh (discovered now) but penalize slightly
        return 80.0
        
    now = datetime.now(timezone.utc)
    delta = now - published_at
    hours_old = delta.total_seconds() / 3600.0
    
    if hours_old < 0:
        # Published in future? Treat as very fresh.
        return 100.0
        
    if hours_old >= max_age_hours:
        return 0.0
        
    # Exponential decay: 100 at 0 hours, approaches 0 at max_age_hours
    # Formula: 100 * (1 - (hours_old / max_age_hours)) ^ 2
    score = 100.0 * math.pow(1.0 - (hours_old / max_age_hours), 2)
    return max(0.0, min(100.0, score))


def filter_stale(candidates: List[RawCandidate], max_age_hours: int = 72) -> List[RawCandidate]:
    """Remove candidates older than max_age_hours."""
    fresh_candidates = []
    
    for candidate in candidates:
        if compute_freshness(candidate.published_at, max_age_hours) > 0:
            fresh_candidates.append(candidate)
            
    return fresh_candidates
