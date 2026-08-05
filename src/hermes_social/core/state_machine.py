"""Domain state machines and lifecycle transition validation for Hermes Social Agent."""

from enum import Enum
from typing import Dict, Set, Union
from hermes_social.constants import (
    ContentIdeaStatus,
    PostStatus,
    StrategyRuleStatus,
    TopicStatus,
)


class InvalidTransitionError(Exception):
    """Raised when an invalid lifecycle state transition is attempted."""

    def __init__(self, entity_type: str, from_state: str, to_state: str) -> None:
        self.entity_type = entity_type
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid {entity_type} transition from '{from_state}' to '{to_state}'"
        )


# 1. Topic lifecycle transitions
TOPIC_TRANSITIONS: Dict[str, Set[str]] = {
    TopicStatus.DISCOVERED.value: {
        TopicStatus.EVALUATING.value,
        TopicStatus.REJECTED.value,
    },
    TopicStatus.EVALUATING.value: {
        TopicStatus.ACCEPTED.value,
        TopicStatus.REJECTED.value,
    },
    TopicStatus.ACCEPTED.value: {
        TopicStatus.RESEARCHING.value,
        TopicStatus.REJECTED.value,
    },
    TopicStatus.RESEARCHING.value: {
        TopicStatus.RESEARCHED.value,
        TopicStatus.REJECTED.value,
    },
    TopicStatus.RESEARCHED.value: {
        TopicStatus.WRITING.value,
        TopicStatus.REJECTED.value,
        TopicStatus.ARCHIVED.value,
    },
    TopicStatus.WRITING.value: {
        TopicStatus.WRITTEN.value,
        TopicStatus.REJECTED.value,
    },
    TopicStatus.WRITTEN.value: {
        TopicStatus.ARCHIVED.value,
    },
    TopicStatus.REJECTED.value: {
        TopicStatus.ARCHIVED.value,
    },
    TopicStatus.ARCHIVED.value: set(),
}

# 2. Post lifecycle transitions
POST_TRANSITIONS: Dict[str, Set[str]] = {
    PostStatus.DRAFT.value: {
        PostStatus.READY_FOR_APPROVAL.value,
        PostStatus.REJECTED.value,
    },
    PostStatus.READY_FOR_APPROVAL.value: {
        PostStatus.APPROVED.value,
        PostStatus.REJECTED.value,
        PostStatus.DRAFT.value,
    },
    PostStatus.APPROVED.value: {
        PostStatus.SCHEDULED.value,
        PostStatus.READY_FOR_MANUAL_PUBLISH.value,
    },
    PostStatus.SCHEDULED.value: {
        PostStatus.PUBLISHED.value,
        PostStatus.FAILED.value,
        PostStatus.READY_FOR_MANUAL_PUBLISH.value,
    },
    PostStatus.READY_FOR_MANUAL_PUBLISH.value: {
        PostStatus.PUBLISHED.value,
        PostStatus.FAILED.value,
    },
    PostStatus.PUBLISHED.value: set(),
    PostStatus.REJECTED.value: {
        PostStatus.DRAFT.value,
    },
    PostStatus.FAILED.value: {
        PostStatus.SCHEDULED.value,
        PostStatus.READY_FOR_MANUAL_PUBLISH.value,
    },
}

# 3. Content Idea lifecycle transitions
CONTENT_IDEA_TRANSITIONS: Dict[str, Set[str]] = {
    ContentIdeaStatus.DRAFT.value: {
        ContentIdeaStatus.APPROVED.value,
        ContentIdeaStatus.REJECTED.value,
    },
    ContentIdeaStatus.APPROVED.value: {
        ContentIdeaStatus.WRITING.value,
        ContentIdeaStatus.REJECTED.value,
    },
    ContentIdeaStatus.WRITING.value: {
        ContentIdeaStatus.COMPLETED.value,
        ContentIdeaStatus.REJECTED.value,
    },
    ContentIdeaStatus.COMPLETED.value: set(),
    ContentIdeaStatus.REJECTED.value: {
        ContentIdeaStatus.DRAFT.value,
    },
}

# 4. Strategy Rule lifecycle transitions
STRATEGY_RULE_TRANSITIONS: Dict[str, Set[str]] = {
    StrategyRuleStatus.HYPOTHESIS.value: {
        StrategyRuleStatus.TESTING.value,
        StrategyRuleStatus.RETIRED.value,
    },
    StrategyRuleStatus.TESTING.value: {
        StrategyRuleStatus.PROVISIONAL.value,
        StrategyRuleStatus.RETIRED.value,
    },
    StrategyRuleStatus.PROVISIONAL.value: {
        StrategyRuleStatus.CONFIRMED.value,
        StrategyRuleStatus.RETIRED.value,
        StrategyRuleStatus.TESTING.value,
    },
    StrategyRuleStatus.CONFIRMED.value: {
        StrategyRuleStatus.RETIRED.value,
    },
    StrategyRuleStatus.RETIRED.value: set(),
}


def _to_str(val: Union[str, Enum]) -> str:
    return val.value if isinstance(val, Enum) else str(val)


def validate_transition(
    entity_type: str,
    from_state: Union[str, Enum],
    to_state: Union[str, Enum],
    transitions_map: Dict[str, Set[str]],
) -> None:
    """Validate a lifecycle transition against a defined transition map."""
    from_str = _to_str(from_state)
    to_str = _to_str(to_state)

    allowed = transitions_map.get(from_str, set())
    if to_str not in allowed:
        raise InvalidTransitionError(entity_type, from_str, to_str)


def validate_topic_transition(
    from_state: Union[TopicStatus, str],
    to_state: Union[TopicStatus, str],
) -> None:
    """Validate a Topic status transition."""
    validate_transition("Topic", from_state, to_state, TOPIC_TRANSITIONS)


def validate_post_transition(
    from_state: Union[PostStatus, str],
    to_state: Union[PostStatus, str],
) -> None:
    """Validate a Post status transition."""
    validate_transition("Post", from_state, to_state, POST_TRANSITIONS)


def validate_content_idea_transition(
    from_state: Union[ContentIdeaStatus, str],
    to_state: Union[ContentIdeaStatus, str],
) -> None:
    """Validate a ContentIdea status transition."""
    validate_transition("ContentIdea", from_state, to_state, CONTENT_IDEA_TRANSITIONS)


def validate_strategy_rule_transition(
    from_state: Union[StrategyRuleStatus, str],
    to_state: Union[StrategyRuleStatus, str],
) -> None:
    """Validate a StrategyRule status transition."""
    validate_transition(
        "StrategyRule", from_state, to_state, STRATEGY_RULE_TRANSITIONS
    )
