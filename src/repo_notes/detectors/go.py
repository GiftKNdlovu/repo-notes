"""Go language detector."""

from .base import ExtensionDetector, LanguageInfo

GO_INFO = LanguageInfo(
    name="go",
    category="backend",
    extensions=frozenset({".go", ".mod", ".sum"}),
)


class GoDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(GO_INFO)
