"""Detector registry for data-driven language classification."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .base import LanguageInfo

# Pre-defined Language Info constants
PYTHON_INFO = LanguageInfo("python", "backend", frozenset({".py", ".pyi", ".pyx", ".pxd", ".pxi", ".ipynb"}))
JS_INFO = LanguageInfo("javascript", "frontend", frozenset({".js", ".jsx", ".mjs", ".cjs"}))
TS_INFO = LanguageInfo("typescript", "frontend", frozenset({".ts", ".tsx", ".mts", ".cts"}))
GO_INFO = LanguageInfo("go", "backend", frozenset({".go"}))
RUST_INFO = LanguageInfo("rust", "systems", frozenset({".rs"}))
JAVA_INFO = LanguageInfo("java", "backend", frozenset({".java", ".jar", ".war"}))
C_CPP_INFO = LanguageInfo("c/c++", "systems", frozenset({".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}))
RUBY_INFO = LanguageInfo("ruby", "backend", frozenset({".rb", ".rake", ".gemspec"}))
PHP_INFO = LanguageInfo("php", "backend", frozenset({".php", ".phtml", ".php5", ".php7"}))
SWIFT_INFO = LanguageInfo("swift", "mobile", frozenset({".swift"}))
KOTLIN_INFO = LanguageInfo("kotlin", "mobile", frozenset({".kt", ".kts"}))
R_LANG_INFO = LanguageInfo("r", "data", frozenset({".r", ".rmd"}))
SHELL_INFO = LanguageInfo("shell", "infra", frozenset({".sh", ".bash", ".zsh", ".fish", ".ps1"}))
SQL_INFO = LanguageInfo("sql", "database", frozenset({".sql"}))
DOCKER_INFO = LanguageInfo("docker", "infra", frozenset({".dockerfile"}))

_DOCKER_FILENAMES = frozenset({
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "docker-compose.override.yml", "docker-compose.override.yaml",
})


@dataclass
class DetectorRegistry:
    _languages: list[LanguageInfo] = field(default_factory=list)
    _extension_map: dict[str, LanguageInfo] = field(default_factory=dict)
    _filename_map: dict[str, LanguageInfo] = field(default_factory=dict)

    def register(self, info: LanguageInfo, filenames: set[str] | frozenset[str] | None = None) -> None:
        if info not in self._languages:
            self._languages.append(info)
        for ext in info.extensions:
            self._extension_map[ext.lower()] = info
        if filenames:
            for fname in filenames:
                self._filename_map[fname.lower()] = info

    def get_for_extension(self, ext: str) -> LanguageInfo | None:
        return self._extension_map.get(ext.lower())

    def classify(self, path: Path) -> LanguageInfo | None:
        name_lower = path.name.lower()
        if name_lower in self._filename_map:
            return self._filename_map[name_lower]
        ext = path.suffix.lower()
        return self._extension_map.get(ext)

    def get_enabled(self, enabled: list[str]) -> DetectorRegistry:
        """Return new registry with only enabled detectors."""
        if "all" in enabled:
            return self
        enabled_set = {e.lower() for e in enabled}
        new_registry = DetectorRegistry()
        for info in self._languages:
            if info.name.lower() in enabled_set:
                fnames = {fname for fname, lang in self._filename_map.items() if lang == info}
                new_registry.register(info, filenames=fnames if fnames else None)
        return new_registry


_registry: DetectorRegistry | None = None


def get_registry() -> DetectorRegistry:
    global _registry
    if _registry is None:
        _registry = DetectorRegistry()
        _register_builtin(_registry)
    return _registry


def _register_builtin(registry: DetectorRegistry) -> None:
    registry.register(PYTHON_INFO)
    registry.register(JS_INFO)
    registry.register(TS_INFO)
    registry.register(GO_INFO)
    registry.register(RUST_INFO)
    registry.register(JAVA_INFO)
    registry.register(C_CPP_INFO)
    registry.register(RUBY_INFO)
    registry.register(PHP_INFO)
    registry.register(SWIFT_INFO)
    registry.register(KOTLIN_INFO)
    registry.register(R_LANG_INFO)
    registry.register(SHELL_INFO)
    registry.register(SQL_INFO)
    registry.register(DOCKER_INFO, filenames=_DOCKER_FILENAMES)
