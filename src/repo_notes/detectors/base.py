"""Base language detector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class LanguageInfo:
    name: str
    category: str
    extensions: frozenset[str]


class LanguageDetector(ABC):
    """Abstract base for language detectors."""

    @property
    @abstractmethod
    def language_info(self) -> LanguageInfo:
        """Return language metadata."""

    @abstractmethod
    def classify(self, path: Path, content_preview: str | None = None) -> LanguageInfo | None:
        """Classify a file. Return LanguageInfo if this detector handles it."""


class ExtensionDetector(LanguageDetector):
    """Base detector that matches by file extension."""

    def __init__(self, language_info: LanguageInfo):
        self._info = language_info

    @property
    def language_info(self) -> LanguageInfo:
        return self._info

    def classify(self, path: Path, content_preview: str | None = None) -> LanguageInfo | None:
        if path.suffix.lower() in self._info.extensions:
            return self._info
        return None
