"""Kotlin language detector."""

from .base import ExtensionDetector, LanguageInfo

KOTLIN_INFO = LanguageInfo(
    name="kotlin",
    category="backend",
    extensions=frozenset({".kt", ".kts"}),
)


class KotlinDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(KOTLIN_INFO)
