"""Swift language detector."""

from .base import ExtensionDetector, LanguageInfo

SWIFT_INFO = LanguageInfo(
    name="swift",
    category="backend",
    extensions=frozenset({".swift"}),
)


class SwiftDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(SWIFT_INFO)
