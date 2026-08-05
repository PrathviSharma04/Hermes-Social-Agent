"""Seeds the brand_rules table from the brand.yaml configuration."""

import sqlite3

from hermes_social.services.brand import BrandSystem


def seed_brand_rules(
    conn: sqlite3.Connection,
    brand: BrandSystem,
    clear_existing: bool = False,
) -> int:
    """Populate brand_rules table from the loaded brand system."""
    
    if clear_existing:
        conn.execute("DELETE FROM brand_rules")
    
    rules_added = 0
    cursor = conn.cursor()

    # Helper to insert
    def _insert(name: str, text: str):
        nonlocal rules_added
        cursor.execute(
            "INSERT INTO brand_rules (rule_name, rule_text, is_active) VALUES (?, ?, 1)",
            (name, text)
        )
        rules_added += 1

    # Seed Banned Phrases
    for phrase in brand.banned_patterns.phrases:
        _insert(f"BANNED_PHRASE: {phrase}", f"Do not use the exact phrase: '{phrase}'")

    # Seed Banned Behaviors
    for behavior in brand.banned_patterns.behaviors:
        _insert(f"BANNED_BEHAVIOR: {behavior[:30]}...", behavior)

    # Seed Content Pillars
    for pillar in brand.content_pillars:
        _insert(f"PILLAR: {pillar.name}", f"Description: {pillar.description}. Keywords: {', '.join(pillar.keywords)}")

    # Seed Visual Families
    for family in brand.visual_families:
        _insert(f"VISUAL_FAMILY: {family.name}", f"Description: {family.description}. Use cases: {', '.join(family.use_cases)}")

    conn.commit()
    return rules_added
