"""Abstract base class for trend source adapters."""

from abc import ABC, abstractmethod
from typing import List

from hermes_social.trends.models import RawCandidate


class SourceAdapter(ABC):
    """Protocol for trend source adapters."""

    def __init__(self, authority: float) -> None:
        """Initialize with a base authority score for this source."""
        self._authority_score = authority

    @abstractmethod
    def fetch_candidates(self, limit: int = 30) -> List[RawCandidate]:
        """Fetch raw candidates from the source."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier (e.g., 'rss', 'hackernews')."""
        pass

    @property
    def authority_score(self) -> float:
        """Return the default authority score for this source (0-100)."""
        return self._authority_score
