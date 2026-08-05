"""Tests for the Brand Brain system (Component 3, 4, 5)."""

import sqlite3
from typing import Any
import pytest

from hermes_social.services.brand import (
    BrandSystem,
    get_visual_family,
    is_pillar_match,
)
from hermes_social.services.brand_validator import validate_brand_compliance
from hermes_social.services.brand_seeder import seed_brand_rules


def test_brand_yaml_loads_successfully(brand_system: BrandSystem) -> None:
    """Verify that brand.yaml loads into the BrandSystem dataclass correctly."""
    assert isinstance(brand_system, BrandSystem)
    assert brand_system.identity.creator_name == "Prathvi Sharma"


def test_brand_identity_fields(brand_system: BrandSystem) -> None:
    """Verify identity fields are populated."""
    assert len(brand_system.identity.expertise) > 0
    assert "primary" in brand_system.identity.audience
    assert len(brand_system.identity.values) > 0


def test_content_pillars_defined(brand_system: BrandSystem) -> None:
    """Verify at least 3 content pillars exist with keywords."""
    assert len(brand_system.content_pillars) >= 3
    for pillar in brand_system.content_pillars:
        assert pillar.name
        assert len(pillar.keywords) > 0


def test_visual_families_defined(brand_system: BrandSystem) -> None:
    """Verify visual families are defined and well-formed."""
    assert len(brand_system.visual_families) >= 3
    for family in brand_system.visual_families:
        assert family.name
        assert family.use_cases


def test_visual_family_lookup(brand_system: BrandSystem) -> None:
    """Test lookup of visual family by name."""
    family = get_visual_family(brand_system, "Editorial Explainer")
    assert family is not None
    assert family.name == "Editorial Explainer"
    
    missing = get_visual_family(brand_system, "Unknown Family")
    assert missing is None


def test_pillar_match(brand_system: BrandSystem) -> None:
    """Test text matching against pillar keywords."""
    # "agentic AI" is a keyword for "AI & Agentic Systems"
    assert is_pillar_match(brand_system, "Building an agentic AI system") is True
    assert is_pillar_match(brand_system, "Cooking a great meal") is False


def test_banned_phrase_detection(brand_system: BrandSystem) -> None:
    """Test that validate_brand_compliance detects banned phrases."""
    text_with_banned = "This new tool is a game changer for everyone."
    result = validate_brand_compliance(text_with_banned, brand_system)
    
    assert not result.passed
    assert any("game changer" in v.lower() for v in result.violations)


def test_clean_text_passes_validation(brand_system: BrandSystem) -> None:
    """Test that clean text passes deterministic validation."""
    clean_text = "Here is a breakdown of how we implemented the new architecture."
    result = validate_brand_compliance(clean_text, brand_system)
    
    assert result.passed
    assert result.score == 100.0
    assert len(result.violations) == 0


def test_hashtag_limit_enforcement(brand_system: BrandSystem) -> None:
    """Test that > 5 hashtags triggers a violation."""
    heavy_hashtags = "Great day #coding #python #web #design #ai #agent"
    result = validate_brand_compliance(heavy_hashtags, brand_system)
    
    assert not result.passed
    assert any("excessive hashtags" in v.lower() for v in result.violations)


def test_brand_seeder_populates_db(db_conn: sqlite3.Connection, brand_system: BrandSystem) -> None:
    """Test that brand.yaml rules are correctly seeded into the database."""
    added = seed_brand_rules(db_conn, brand_system)
    assert added > 10  # Should be many rules (phrases + behaviors + pillars + visual families)
    
    cursor = db_conn.execute("SELECT count(*) FROM brand_rules WHERE is_active = 1")
    count = cursor.fetchone()[0]
    assert count == added

    # Verify a specific rule was added
    cursor = db_conn.execute("SELECT rule_name FROM brand_rules WHERE rule_name LIKE 'BANNED_PHRASE:%' LIMIT 1")
    row = cursor.fetchone()
    assert row is not None
