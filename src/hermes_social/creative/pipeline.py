"""Creative Pipeline Orchestration."""

import logging
import sqlite3
from pathlib import Path
from typing import Dict

from hermes_social.constants import PostStatus
from hermes_social.creative.director import generate_creative_brief
from hermes_social.creative.providers import get_image_provider
from hermes_social.creative.renderer import render_carousel

logger = logging.getLogger(__name__)


def generate_assets_for_post(
    conn: sqlite3.Connection,
    post: dict,
    brand_context: dict,
    output_base_dir: Path,
    model_route: str = "gemini/gemini-1.5-pro",
    image_provider_type: str = "mock"
) -> bool:
    """Execute the full creative pipeline for a post."""
    
    post_id = post["id"]
    
    # 1. Generate Creative Brief
    brief = generate_creative_brief(conn, post["body"], post["platform"], brand_context, model_route)
    
    # 2. Setup paths
    post_dir = output_base_dir / str(post_id)
    post_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Request Images
    provider = get_image_provider(image_provider_type)
    image_paths: Dict[int, str] = {}
    
    for slide in brief.slides:
        if slide.image_prompt:
            output_path = post_dir / f"raw_bg_{slide.slide_number}.png"
            final_path = provider.generate_image(
                prompt=slide.image_prompt,
                dimensions=brief.dimensions,
                output_path=str(output_path)
            )
            image_paths[slide.slide_number] = final_path
            
    # 4. Render Final Assets
    rendered_paths = render_carousel(brief, image_paths, post_dir / "renders")
    
    # 5. Save to database
    for path in rendered_paths:
        conn.execute(
            """
            INSERT INTO assets (post_id, asset_type, path, qa_status)
            VALUES (?, ?, ?, ?)
            """,
            (post_id, brief.format, path, "PENDING")
        )
        
    conn.execute(
        """
        UPDATE posts SET status = ? WHERE id = ?
        """,
        (PostStatus.READY_FOR_APPROVAL.value, post_id)
    )
    conn.commit()
    
    return True
