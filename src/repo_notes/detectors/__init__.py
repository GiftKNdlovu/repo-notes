"""Language detectors package."""

from .base import LanguageDetector, LanguageInfo
from .registry import DetectorRegistry, get_registry

__all__ = ["LanguageDetector", "LanguageInfo", "DetectorRegistry", "get_registry"]
