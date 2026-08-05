"""Brand loader service for Hermes Social Agent.

Loads and validates the brand.yaml configuration into typed dataclasses.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class BrandIdentity:
    creator_name: str
    brand_purpose: str
    positioning: str
    expertise: List[str]
    audience: Dict[str, Any]
    values: List[str]
    differentiators: List[str]
    desired_perception: List[str]


@dataclass
class ContentPillar:
    name: str
    description: str
    keywords: List[str]


@dataclass
class VoiceConfig:
    sentence_style: str
    vocabulary: str
    technical_depth: str
    humor_policy: str
    opinion_policy: str
    punctuation: str
    opening_styles: List[str]
    closing_styles: List[str]


@dataclass
class BannedPatterns:
    phrases: List[str]
    behaviors: List[str]


@dataclass
class VisualFamily:
    name: str
    description: str
    bg_style: str
    typography_scale: str
    illustration: str
    use_cases: List[str]


@dataclass
class VisualSystem:
    palette: Dict[str, str]
    typography: Dict[str, str]
    spacing: Dict[str, str]
    borders: Dict[str, str]
    logo: Dict[str, Any]
    platform_dimensions: Dict[str, str]
    accessibility: Dict[str, Any]


@dataclass
class BrandScoring:
    brand_fit_threshold: int
    writing_quality_threshold: int
    visual_quality_threshold: int
    scoring_dimensions: List[str]


@dataclass
class BrandSystem:
    identity: BrandIdentity
    content_pillars: List[ContentPillar]
    voice: VoiceConfig
    banned_patterns: BannedPatterns
    visual_system: VisualSystem
    visual_families: List[VisualFamily]
    scoring: BrandScoring


def load_brand_system(config_path: Path) -> BrandSystem:
    """Load and validate brand.yaml into typed dataclasses."""
    if not config_path.exists():
        raise FileNotFoundError(f"Brand configuration file not found at: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return BrandSystem(
        identity=BrandIdentity(**data["identity"]),
        content_pillars=[ContentPillar(**p) for p in data.get("content_pillars", [])],
        voice=VoiceConfig(**data["voice"]),
        banned_patterns=BannedPatterns(**data["banned_patterns"]),
        visual_system=VisualSystem(**data["visual_system"]),
        visual_families=[VisualFamily(**f) for f in data.get("visual_families", [])],
        scoring=BrandScoring(**data["scoring"]),
    )


def get_visual_family(brand: BrandSystem, name: str) -> Optional[VisualFamily]:
    """Look up a visual family by its exact name."""
    for family in brand.visual_families:
        if family.name.lower() == name.lower():
            return family
    return None


def is_pillar_match(brand: BrandSystem, text: str) -> bool:
    """Check if text contains any keywords from any content pillar."""
    text_lower = text.lower()
    for pillar in brand.content_pillars:
        for kw in pillar.keywords:
            if kw.lower() in text_lower:
                return True
    return False
