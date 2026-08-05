"""Deterministic brand compliance validator."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re

from hermes_social.services.brand import BrandSystem


@dataclass
class BrandValidationResult:
    score: float
    passed: bool
    violations: List[str]
    dimension_scores: Dict[str, float] = field(default_factory=dict)


def validate_brand_compliance(
    text: str,
    brand: BrandSystem,
    content_pillar: Optional[str] = None,
    visual_family: Optional[str] = None,
) -> BrandValidationResult:
    """Validate text against deterministic brand rules (banned phrases, hashtag limits, etc.)."""
    violations = []
    text_lower = text.lower()
    
    # Check banned phrases
    for phrase in brand.banned_patterns.phrases:
        if phrase.lower() in text_lower:
            violations.append(f"Banned phrase detected: '{phrase}'")

    # Check hashtag limit (max 5 per post per rules)
    hashtag_count = len(re.findall(r'#\w+', text))
    if hashtag_count > 5:
        violations.append(f"Excessive hashtags: found {hashtag_count}, maximum is 5")

    # Check pillar match if provided
    if content_pillar:
        found_pillar = False
        for pillar in brand.content_pillars:
            if pillar.name.lower() == content_pillar.lower():
                found_pillar = True
                # Very basic check: are any pillar keywords in the text?
                if not any(kw.lower() in text_lower for kw in pillar.keywords):
                    violations.append(f"Text does not appear to align with pillar '{content_pillar}' (no keywords found)")
                break
        if not found_pillar:
            violations.append(f"Unknown content pillar specified: '{content_pillar}'")

    # Determine passing score
    # A simple baseline deterministic score: start at 100, subtract 20 per violation.
    score = max(0.0, 100.0 - (len(violations) * 20.0))
    passed = score >= brand.scoring.brand_fit_threshold

    return BrandValidationResult(
        score=score,
        passed=passed,
        violations=violations,
        dimension_scores={"banned_pattern_absence": score}
    )


def compute_brand_score(
    validation: BrandValidationResult,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute weighted brand score from dimension scores (placeholder for future LLM dimensions)."""
    # Currently deterministic, returns the baseline score
    return validation.score
