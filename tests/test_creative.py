"""Tests for Phase 7 Creative Engine."""

import sqlite3
from pathlib import Path
import pytest

from hermes_social.constants import TopicStatus, PostStatus
from hermes_social.db.repositories.topics import TopicRepository
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.creative.models import CreativeBrief, SlideDesign
from hermes_social.creative.director import generate_creative_brief
from hermes_social.creative.pipeline import generate_assets_for_post


def test_creative_brief_mocked(db_conn: sqlite3.Connection):
    """Test generating a creative brief translates into the correct model."""
    post_content = "Here is some content about Agentic AI."
    brand_context = {"visual_families": ["Editorial Explainer"]}
    
    # We pass 'mock' as the model route.
    # The client execute_prompt needs to support mocking CreativeBrief return.
    
    # Actually, if we use the same execute_prompt mock, it might not know how to mock CreativeBrief.
    # We should patch the execute_prompt for this test.
    import hermes_social.creative.director
    from unittest.mock import patch
    
    mock_brief_data = {
        "format": "carousel",
        "dimensions": [1080, 1080],
        "design_family": "Editorial Explainer",
        "visual_objective": "explain concept",
        "slides": [
            {
                "slide_number": 1,
                "text_content": "Slide 1 text",
                "image_prompt": "A robot thinking",
                "layout_type": "split"
            }
        ],
        "brand_elements": ["Logo"]
    }
    
    with patch("hermes_social.creative.director.execute_prompt", return_value=mock_brief_data):
        brief = generate_creative_brief(db_conn, post_content, "instagram", brand_context, model_route="mock")
        
        assert isinstance(brief, CreativeBrief)
        assert len(brief.slides) == 1
        assert brief.slides[0].image_prompt == "A robot thinking"


def test_pipeline_success(db_conn: sqlite3.Connection, tmp_path: Path):
    """Test the full pipeline with mocked LLM and MockImageProvider."""
    post_repo = PostRepository(db_conn)
    
    # Create dummy topic and content_idea
    cursor = db_conn.execute("INSERT INTO topics (canonical_topic, status) VALUES ('AI', 'RESEARCHED')")
    topic_id = cursor.lastrowid
    
    cursor = db_conn.execute("INSERT INTO content_ideas (topic_id, angle, status) VALUES (?, 'angle', 'APPROVED')", (topic_id,))
    content_idea_id = cursor.lastrowid
    
    post_id = post_repo.create({
        "content_idea_id": content_idea_id,
        "platform": "instagram",
        "body": "Mock content",
        "format": "carousel",
        "status": PostStatus.DRAFT.value,
        "idempotency_key": "test_creative_1"
    })
    
    cursor = db_conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
    columns = [col[0] for col in cursor.description]
    post_data = dict(zip(columns, cursor.fetchone()))
    
    brand_context = {"visual_families": ["Editorial Explainer"]}
    
    mock_brief_data = {
        "format": "carousel",
        "dimensions": [1080, 1080],
        "design_family": "Editorial Explainer",
        "visual_objective": "explain concept",
        "slides": [
            {
                "slide_number": 1,
                "text_content": "Slide 1 text",
                "image_prompt": "A robot thinking",
                "layout_type": "split"
            }
        ],
        "brand_elements": ["Logo"]
    }
    
    from unittest.mock import patch
    with patch("hermes_social.creative.pipeline.generate_creative_brief", return_value=CreativeBrief(**mock_brief_data)):
        success = generate_assets_for_post(
            db_conn, 
            post_data, 
            brand_context, 
            output_base_dir=tmp_path, 
            image_provider_type="mock"
        )
        
        assert success is True
        
        # Verify db updated
        cursor = db_conn.execute("SELECT status FROM posts WHERE id = ?", (post_id,))
        assert cursor.fetchone()[0] == PostStatus.READY_FOR_APPROVAL.value
        
        # Verify assets table updated
        cursor = db_conn.execute("SELECT * FROM assets WHERE post_id = ?", (post_id,))
        assets = cursor.fetchall()
        assert len(assets) == 1
        assert "slide_01.png" in assets[0][3] # path is index 3
        
        # Verify file created
        assert Path(assets[0][3]).exists()
