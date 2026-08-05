"""Tests for domain lifecycle state machine transitions."""

import pytest
from hermes_social.constants import (
    ContentIdeaStatus,
    PostStatus,
    StrategyRuleStatus,
    TopicStatus,
)
from hermes_social.core.state_machine import (
    InvalidTransitionError,
    validate_content_idea_transition,
    validate_post_transition,
    validate_strategy_rule_transition,
    validate_topic_transition,
)


def test_valid_topic_lifecycle() -> None:
    """Test valid sequential status transitions for Topic."""
    validate_topic_transition(TopicStatus.DISCOVERED, TopicStatus.EVALUATING)
    validate_topic_transition(TopicStatus.EVALUATING, TopicStatus.ACCEPTED)
    validate_topic_transition(TopicStatus.ACCEPTED, TopicStatus.RESEARCHING)
    validate_topic_transition(TopicStatus.RESEARCHING, TopicStatus.RESEARCHED)
    validate_topic_transition(TopicStatus.RESEARCHED, TopicStatus.WRITING)
    validate_topic_transition(TopicStatus.WRITING, TopicStatus.WRITTEN)
    validate_topic_transition(TopicStatus.WRITTEN, TopicStatus.ARCHIVED)


def test_invalid_topic_transition() -> None:
    """Test that invalid topic status transitions raise InvalidTransitionError."""
    with pytest.raises(InvalidTransitionError):
        validate_topic_transition(TopicStatus.DISCOVERED, TopicStatus.ARCHIVED)
    with pytest.raises(InvalidTransitionError):
        validate_topic_transition(TopicStatus.REJECTED, TopicStatus.ACCEPTED)


def test_valid_post_lifecycle() -> None:
    """Test valid sequential and revision transitions for Post."""
    validate_post_transition(PostStatus.DRAFT, PostStatus.READY_FOR_APPROVAL)
    validate_post_transition(PostStatus.READY_FOR_APPROVAL, PostStatus.APPROVED)
    validate_post_transition(PostStatus.APPROVED, PostStatus.SCHEDULED)
    validate_post_transition(PostStatus.SCHEDULED, PostStatus.PUBLISHED)

    # Revision loops
    validate_post_transition(PostStatus.READY_FOR_APPROVAL, PostStatus.DRAFT)
    validate_post_transition(PostStatus.REJECTED, PostStatus.DRAFT)


def test_invalid_post_transition() -> None:
    """Test that skipping approval or publishing drafted posts raises InvalidTransitionError."""
    with pytest.raises(InvalidTransitionError):
        validate_post_transition(PostStatus.DRAFT, PostStatus.PUBLISHED)
    with pytest.raises(InvalidTransitionError):
        validate_post_transition(PostStatus.PUBLISHED, PostStatus.DRAFT)


def test_content_idea_transitions() -> None:
    """Test valid and invalid content idea transitions."""
    validate_content_idea_transition(ContentIdeaStatus.DRAFT, ContentIdeaStatus.APPROVED)
    validate_content_idea_transition(ContentIdeaStatus.APPROVED, ContentIdeaStatus.WRITING)
    with pytest.raises(InvalidTransitionError):
        validate_content_idea_transition(ContentIdeaStatus.DRAFT, ContentIdeaStatus.COMPLETED)


def test_strategy_rule_transitions() -> None:
    """Test strategy rule progression from hypothesis to confirmed."""
    validate_strategy_rule_transition(
        StrategyRuleStatus.HYPOTHESIS, StrategyRuleStatus.TESTING
    )
    validate_strategy_rule_transition(
        StrategyRuleStatus.TESTING, StrategyRuleStatus.PROVISIONAL
    )
    validate_strategy_rule_transition(
        StrategyRuleStatus.PROVISIONAL, StrategyRuleStatus.CONFIRMED
    )
    with pytest.raises(InvalidTransitionError):
        validate_strategy_rule_transition(
            StrategyRuleStatus.HYPOTHESIS, StrategyRuleStatus.CONFIRMED
        )
