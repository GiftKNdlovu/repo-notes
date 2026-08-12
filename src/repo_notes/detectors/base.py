"""Base language metadata definitions."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LanguageInfo:
    name: str
    category: str
    extensions: frozenset[str] = field(default_factory=frozenset)
