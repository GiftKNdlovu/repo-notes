"""Java language detector."""

from .base import ExtensionDetector, LanguageInfo

JAVA_INFO = LanguageInfo(
    name="java",
    category="backend",
    extensions=frozenset({".java"}),
)


class JavaDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(JAVA_INFO)
