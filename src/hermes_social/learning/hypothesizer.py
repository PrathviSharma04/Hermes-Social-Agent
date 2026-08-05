"""Hypothesis Generator: Turns observations into DRAFT experiments."""

import logging
import sqlite3
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from hermes_social.config import AppConfig
from hermes_social.db.repositories.experiments import ExperimentRepository
from hermes_social.llm.client import execute_prompt

logger = logging.getLogger(__name__)


class GeneratedHypothesis(BaseModel):
    name: str = Field(..., description="Short title for the experiment")
    hypothesis: str = Field(..., description="The hypothesis being tested")
    platform: str = Field(..., description="The platform (e.g., linkedin, x, telegram)")
    variable: str = Field(..., description="The variable being isolated (e.g., hook_length, time_of_day)")
    variant_a: str = Field(..., description="Description of variant A")
    variant_b: str = Field(..., description="Description of variant B")


class HypothesesList(BaseModel):
    hypotheses: List[GeneratedHypothesis]


def generate_hypotheses(conn: sqlite3.Connection, config: AppConfig, observations: List[Dict[str, Any]]) -> None:
    """
    Takes observations of outliers and asks the LLM to generate testable A/B hypotheses.
    """
    if not observations:
        logger.info("No observations available to generate hypotheses.")
        return
        
    system_prompt = """
    You are an expert Social Media Data Scientist.
    Your goal is to look at a list of recent performance outliers (both high and low) and generate testable A/B hypotheses.
    Do NOT generate hypotheses based on a single post. Look for patterns in formatting, hook length, or content style.
    Generate a maximum of 3 hypotheses.
    """
    
    # Format observations for the prompt
    obs_text = json.dumps(observations, indent=2)
    user_prompt = f"Here are the recent outliers:\n{obs_text}\n\nGenerate testable A/B hypotheses."
    
    try:
        response = execute_prompt(
            conn=conn,
            prompt=user_prompt,
            system_prompt=system_prompt,
            task_type="hypothesis_generation",
            model_route="gemini/gemini-1.5-pro", # Use Gemini for auditing / default structure
            response_format=HypothesesList
        )
    except Exception as e:
        logger.error(f"Failed to generate hypotheses: {e}")
        return
        
    hypotheses = HypothesesList(**response)
    
    if not hypotheses.hypotheses:
        logger.info("LLM generated no hypotheses.")
        return
        
    repo = ExperimentRepository(conn)
    
    for h in hypotheses.hypotheses:
        repo.create({
            "name": h.name,
            "hypothesis": h.hypothesis,
            "platform": h.platform.lower(),
            "variable": h.variable,
            "variant_a": h.variant_a,
            "variant_b": h.variant_b,
            "minimum_samples": 10  # Exit gate constraint: >1
        })
        logger.info(f"Generated DRAFT experiment: {h.name}")
