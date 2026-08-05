"""Deterministic Asset Renderer (Pillow)."""

import logging
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont

from hermes_social.creative.models import CreativeBrief

logger = logging.getLogger(__name__)


def render_carousel(
    brief: CreativeBrief, 
    image_paths: Dict[int, str],
    output_dir: Path
) -> List[str]:
    """
    Renders the final PNG slides using Pillow.
    Handles exact dimensions, safe-areas, and typography.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered_paths = []
    
    width, height = brief.dimensions
    
    # Try to load a nice font, fallback to default
    try:
        # If we had a real downloaded font we'd use it here
        # For MVP we just use default font, but we scale it up
        # font = ImageFont.truetype("arial.ttf", 60)
        import urllib.request
        import os
        
        # Download Inter font if it doesn't exist
        font_path = output_dir / "Inter-Bold.ttf"
        if not font_path.exists():
            url = "https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Bold.ttf"
            urllib.request.urlretrieve(url, font_path)
            
        title_font = ImageFont.truetype(str(font_path), 80)
        body_font = ImageFont.truetype(str(font_path), 50)
    except Exception as e:
        logger.warning(f"Failed to load custom font, falling back: {e}")
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()
    
    for slide in brief.slides:
        # Create base canvas
        img = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # 1. Background image if requested
        bg_path = image_paths.get(slide.slide_number)
        if bg_path and Path(bg_path).exists():
            try:
                bg = Image.open(bg_path).convert('RGB')
                # Simple center crop to fit
                bg_aspect = bg.width / bg.height
                canvas_aspect = width / height
                
                if bg_aspect > canvas_aspect:
                    # bg is wider
                    new_w = int(bg.height * canvas_aspect)
                    left = (bg.width - new_w) // 2
                    bg = bg.crop((left, 0, left + new_w, bg.height))
                else:
                    # bg is taller
                    new_h = int(bg.width / canvas_aspect)
                    top = (bg.height - new_h) // 2
                    bg = bg.crop((0, top, bg.width, top + new_h))
                    
                bg = bg.resize((width, height), Image.Resampling.LANCZOS)
                img.paste(bg, (0, 0))
                
                # Add a dark overlay so text is readable
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 150))
                img.paste(overlay, (0,0), overlay)
                
            except Exception as e:
                logger.error(f"Failed to process background image for slide {slide.slide_number}: {e}")
                
        # 2. Typography
        text_color = (255, 255, 255) if bg_path else (30, 30, 30)
        
        # Simple text wrapping
        words = slide.text_content.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            # Try bounding box
            bbox = draw.textbbox((0,0), " ".join(current_line), font=title_font)
            if bbox[2] > width - 200: # 100px margins
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        # Draw text
        y_text = height // 3
        for line in lines:
            bbox = draw.textbbox((0,0), line, font=title_font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            draw.text(((width - line_width) / 2, y_text), line, font=title_font, fill=text_color)
            y_text += line_height + 20
            
        # 3. Slide Number & Brand
        draw.text((100, height - 150), f"Slide {slide.slide_number}/{len(brief.slides)}", font=body_font, fill=text_color)
        if brief.brand_elements:
            draw.text((width - 400, height - 150), brief.brand_elements[0], font=body_font, fill=text_color)
            
        # Save output
        output_file = output_dir / f"slide_{slide.slide_number:02d}.png"
        img.save(output_file)
        rendered_paths.append(str(output_file))
        
    return rendered_paths
