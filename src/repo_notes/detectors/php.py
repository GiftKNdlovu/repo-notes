"""PHP language detector."""

from .base import ExtensionDetector, LanguageInfo

PHP_INFO = LanguageInfo(
    name="php",
    category="backend",
    extensions=frozenset({".php", ".phtml", ".php3", ".php4", ".php5"}),
)


class PhpDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(PHP_INFO)
