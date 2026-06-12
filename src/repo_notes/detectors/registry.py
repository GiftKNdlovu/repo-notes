"""Detector registry for auto-discovery."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import LanguageDetector, LanguageInfo


@dataclass
class DetectorRegistry:
    _detectors: list[LanguageDetector] = field(default_factory=list)
    _extension_map: dict[str, LanguageDetector] = field(default_factory=dict)

    def register(self, detector: LanguageDetector) -> None:
        self._detectors.append(detector)
        for ext in detector.language_info.extensions:
            self._extension_map[ext] = detector

    def get_for_extension(self, ext: str) -> LanguageDetector | None:
        return self._extension_map.get(ext.lower())

    def classify(self, path: Path, content_preview: str | None = None) -> LanguageInfo | None:
        ext = path.suffix.lower()
        detector = self._extension_map.get(ext)
        if detector:
            return detector.classify(path, content_preview)
        for detector in self._detectors:
            result = detector.classify(path, content_preview)
            if result:
                return result
        return None

    def get_enabled(self, enabled: list[str]) -> DetectorRegistry:
        """Return new registry with only enabled detectors."""
        if "all" in enabled:
            return self
        new_registry = DetectorRegistry()
        for detector in self._detectors:
            if detector.language_info.name.lower() in enabled:
                new_registry.register(detector)
        return new_registry


_registry: DetectorRegistry | None = None


def get_registry() -> DetectorRegistry:
    global _registry
    if _registry is None:
        _registry = DetectorRegistry()
        _register_builtin(_registry)
    return _registry


def _register_builtin(registry: DetectorRegistry) -> None:
    from . import python, javascript, go, rust
    registry.register(python.PythonDetector())
    registry.register(javascript.JavaScriptDetector())
    registry.register(go.GoDetector())
    registry.register(rust.RustDetector())