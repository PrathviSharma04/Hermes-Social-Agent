"""Fetch web source content for research."""

import logging
import re
from typing import Dict, List
import requests

from hermes_social.research.models import FetchedSource

logger = logging.getLogger(__name__)


def fetch_all_sources(topic_sources: List[Dict], timeout: int = 10) -> List[FetchedSource]:
    """Fetch content for all topic sources, handling errors gracefully."""
    fetched = []
    
    # Standard headers to avoid basic blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for src in topic_sources:
        url = src.get("url")
        if not url:
            continue
            
        source_id = src.get("id", 0)
        authority = src.get("authority_score", 50.0)
        published_at = src.get("published_at")
        title = src.get("source_name", "Unknown Source")
        
        # For Reddit API links, we shouldn't scrape the JSON directly as HTML. 
        # But for now, we'll just try to fetch the URL.
        try:
            logger.info(f"Fetching source: {url}")
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            
            # Very basic HTML stripping
            raw_html = resp.text
            # Extract basic text (remove script/style, then tags)
            text = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', raw_html, flags=re.IGNORECASE | re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', text)
            # Clean whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit to first ~5000 chars for deterministic processing
            text_content = text[:5000]
            
            fetched.append(FetchedSource(
                url=url,
                title=title,
                text_content=text_content,
                published_at=published_at,
                fetch_status="ok",
                authority_score=authority,
                source_id=source_id,
            ))
            
        except requests.Timeout:
            logger.warning(f"Timeout fetching {url}")
            fetched.append(FetchedSource(url, title, "", published_at, "timeout", authority, source_id))
        except requests.RequestException as e:
            logger.warning(f"Error fetching {url}: {e}")
            fetched.append(FetchedSource(url, title, "", published_at, "error", authority, source_id))
            
    return fetched
