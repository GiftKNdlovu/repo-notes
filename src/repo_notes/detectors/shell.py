"""Shell/scripting language detector."""

from .base import ExtensionDetector, LanguageInfo

SHELL_INFO = LanguageInfo(
    name="shell",
    category="scripting",
    extensions=frozenset({".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd"}),
)


class ShellDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(SHELL_INFO)
