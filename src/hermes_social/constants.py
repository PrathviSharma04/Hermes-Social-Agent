"""Application constants and enumerations for Hermes Social Agent."""

from enum import Enum


class Environment(str, Enum):
    """Application runtime environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class SourceType(str, Enum):
    """Trend discovery source types."""
    RSS = "rss"
    HACKERNEWS = "hackernews"
    DEVTO = "devto"
    REDDIT = "reddit"


class ApprovalMode(str, Enum):
    """Post approval mode settings."""
    REQUIRED = "REQUIRED"
    AUTO = "AUTO"


class Platform(str, Enum):
    """Supported social media platforms."""
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    X = "x"


class PostStatus(str, Enum):
    """Post lifecycle statuses."""
    DRAFT = "DRAFT"
    READY_FOR_APPROVAL = "READY_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    READY_FOR_MANUAL_PUBLISH = "READY_FOR_MANUAL_PUBLISH"
    FAILED = "FAILED"


class TopicStatus(str, Enum):
    """Topic lifecycle statuses."""
    DISCOVERED = "DISCOVERED"
    EVALUATING = "EVALUATING"
    ACCEPTED = "ACCEPTED"
    RESEARCHING = "RESEARCHING"
    RESEARCHED = "RESEARCHED"
    WRITING = "WRITING"
    WRITTEN = "WRITTEN"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class ResearchStatus(str, Enum):
    """Research run statuses."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ClaimType(str, Enum):
    """Claim classification types."""
    FACT = "FACT"
    OPINION = "OPINION"
    PREDICTION = "PREDICTION"
    PERSONAL_EXPERIENCE = "PERSONAL_EXPERIENCE"


class VerificationStatus(str, Enum):
    """Claim verification statuses."""
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    DISPUTED = "DISPUTED"
    RETRACTED = "RETRACTED"


class ContentIdeaStatus(str, Enum):
    """Content idea lifecycle statuses."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    WRITING = "WRITING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class PostFormat(str, Enum):
    """Social post format types."""
    TEXT = "TEXT"
    SINGLE_IMAGE = "SINGLE_IMAGE"
    CAROUSEL = "CAROUSEL"
    THREAD = "THREAD"
    DOCUMENT = "DOCUMENT"


class AssetType(str, Enum):
    """Creative asset types."""
    IMAGE = "IMAGE"
    CAROUSEL_SLIDE = "CAROUSEL_SLIDE"
    THUMBNAIL = "THUMBNAIL"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"


class QAStatus(str, Enum):
    """Creative asset QA statuses."""
    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"


class PerformanceWindow(str, Enum):
    """Performance snapshot capture time windows."""
    HOUR_2 = "2h"
    HOUR_24 = "24h"
    HOUR_72 = "72h"
    DAY_7 = "7d"


class ExperimentStatus(str, Enum):
    """Experiment lifecycle statuses."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StrategyRuleStatus(str, Enum):
    """Strategy rule lifecycle statuses."""
    HYPOTHESIS = "HYPOTHESIS"
    TESTING = "TESTING"
    PROVISIONAL = "PROVISIONAL"
    CONFIRMED = "CONFIRMED"
    RETIRED = "RETIRED"


class ScheduledActionStatus(str, Enum):
    """Scheduled action lifecycle statuses."""
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class SystemEventLevel(str, Enum):
    """System event audit log levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class TelegramIntent(str, Enum):
    """Parsed user intent from natural language commands via Telegram."""
    QUERY_STATUS = "QUERY_STATUS"
    QUERY_PERFORMANCE = "QUERY_PERFORMANCE"
    QUERY_LEARNINGS = "QUERY_LEARNINGS"
    QUERY_RESEARCH = "QUERY_RESEARCH"
    CREATE_TOPIC = "CREATE_TOPIC"
    CREATE_POST = "CREATE_POST"
    SCHEDULE_POST = "SCHEDULE_POST"
    RESCHEDULE_POST = "RESCHEDULE_POST"
    CANCEL_POST = "CANCEL_POST"
    PAUSE_PLATFORM = "PAUSE_PLATFORM"
    RESUME_PLATFORM = "RESUME_PLATFORM"
    PAUSE_PUBLISHING = "PAUSE_PUBLISHING"
    RESUME_PUBLISHING = "RESUME_PUBLISHING"
    PAUSE_AUTOPILOT = "PAUSE_AUTOPILOT"
    RESUME_AUTOPILOT = "RESUME_AUTOPILOT"
    APPROVE_POST = "APPROVE_POST"
    REJECT_POST = "REJECT_POST"
    REVISE_POST = "REVISE_POST"
    REVISE_ASSET = "REVISE_ASSET"
    CHANGE_FORMAT = "CHANGE_FORMAT"
    FORCE_RESEARCH = "FORCE_RESEARCH"
    FORCE_ANALYSIS = "FORCE_ANALYSIS"
    EMERGENCY_STOP = "EMERGENCY_STOP"  # Halts everything: publishing, research, generation
    UNKNOWN = "UNKNOWN"


class PublishMethod(str, Enum):
    """Method used for publishing the post."""
    API_AUTOMATED = "API_AUTOMATED"
    MANUAL_FALLBACK = "MANUAL_FALLBACK"

