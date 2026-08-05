"""LLM Client Wrapper."""

import json
import logging
import sqlite3
from typing import Any, Dict, Optional, Type
import time
import litellm

logger = logging.getLogger(__name__)


def execute_prompt(
    conn: sqlite3.Connection,
    prompt: str,
    system_prompt: str,
    task_type: str,
    model_route: str = "gemini/gemini-1.5-pro",
    response_format: Optional[Type] = None,
) -> Dict[str, Any]:
    """Execute an LLM prompt, parse JSON, and log metadata to model_runs."""
    
    start_time = time.time()
    success = False
    error_msg = None
    parsed_response = {}
    tokens_used = 0
    
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # If a Pydantic model is provided, enforce JSON mode natively if supported,
        # but for maximum compatibility we just ask for JSON in the prompt and parse it.
        # LiteLLM does support response_format={"type": "json_object"} for supported models.
        kwargs = {}
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}
            
        # In a real scenario, API keys are loaded via os.environ by dotenv in cli.py
        # For tests, litellm requires the key to exist or be mocked
        if "mock" in model_route.lower():
            # Mock mode for tests
            parsed_response = _mock_response(task_type)
            success = True
            tokens_used = 100
        else:
            # Note: During the tests this shouldn't be called unless explicitly testing LLM
            response = litellm.completion(
                model=model_route,
                messages=messages,
                **kwargs
            )
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            if response_format:
                try:
                    # Clean markdown code blocks if present
                    if content.startswith("```json"):
                        content = content.split("```json")[1].rsplit("```", 1)[0].strip()
                    elif content.startswith("```"):
                        content = content.split("```")[1].rsplit("```", 1)[0].strip()
                    parsed_response = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM JSON response: {e}\nContent: {content}")
                    raise ValueError(f"LLM did not return valid JSON: {e}")
            else:
                parsed_response = {"content": content}
                
            success = True
            
    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"LLM Execution failed: {e}")
        raise
    finally:
        end_time = time.time()
        _log_model_run(
            conn, 
            task_type=task_type, 
            model_route=model_route, 
            start_time=start_time, 
            end_time=end_time, 
            success=success, 
            tokens_used=tokens_used, 
            error_msg=error_msg
        )
        
    return parsed_response


def _log_model_run(
    conn: sqlite3.Connection,
    task_type: str,
    model_route: str,
    start_time: float,
    end_time: float,
    success: bool,
    tokens_used: int,
    error_msg: Optional[str]
):
    """Log the execution to the model_runs table."""
    try:
        conn.execute(
            """
            INSERT INTO model_runs (
                task_type, model_route, started_at, ended_at, 
                success, tokens_used, error
            ) VALUES (
                ?, ?, datetime(?, 'unixepoch'), datetime(?, 'unixepoch'),
                ?, ?, ?
            )
            """,
            (
                task_type,
                model_route,
                start_time,
                end_time,
                1 if success else 0,
                tokens_used,
                error_msg
            )
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to log model run: {e}")


def _mock_response(task_type: str) -> dict:
    """Provide deterministic mock responses for testing."""
    if task_type == "creative_brief":
        return {
            "format": "carousel",
            "dimensions": [1080, 1080],
            "design_family": "Editorial Explainer",
            "visual_objective": "Mock objective",
            "slides": [
                {
                    "slide_number": 1,
                    "text_content": "Mock Slide 1 Text",
                    "image_prompt": "Mock background prompt",
                    "layout_type": "full_image"
                }
            ],
            "brand_elements": ["Logo"]
        }
    elif task_type == "master_narrative":
        return {
            "hook": "Mock Hook",
            "core_thesis": "Mock Thesis",
            "why_it_matters": "Mock Matters",
            "evidence": ["Mock Evidence 1"],
            "insight": "Mock Insight",
            "practical_takeaway": "Mock Takeaway",
            "optional_cta": "Mock CTA"
        }
    elif task_type.startswith("adapter"):
        return {
            "platform": task_type.split("_")[1],
            "text_content": "Mock Adapted Content",
            "format_type": "text",
            "media_requirements": None
        }
    elif task_type == "content_council":
        return {
            "Research Critic": {"score": 90, "critique": "Good", "critical_flags": []},
            "Skeptic": {"score": 85, "critique": "Fine", "critical_flags": []},
            "Audience Critic": {"score": 88, "critique": "Relevant", "critical_flags": []},
            "Human-Writing Critic": {"score": 88, "critique": "Acceptable", "critical_flags": []},
            "Brand Critic": {"score": 95, "critique": "On brand", "critical_flags": []},
            "Growth Critic": {"score": 80, "critique": "Solid", "critical_flags": []}
        }
    elif task_type == "editor_in_chief":
        return {
            "decision": "PASS",
            "revision_notes": None,
            "final_scores": {"writing": 85, "brand": 95}
        }
    return {"content": "Mock content"}
