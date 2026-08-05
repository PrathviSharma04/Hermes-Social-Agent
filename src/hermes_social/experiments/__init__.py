"""Experiment Engine for A/B testing variables and promoting winning strategies."""

from hermes_social.experiments.engine import start_experiment, assign_post, evaluate_experiment
from hermes_social.experiments.strategy import promote_to_strategy

__all__ = [
    "start_experiment",
    "assign_post",
    "evaluate_experiment",
    "promote_to_strategy"
]
