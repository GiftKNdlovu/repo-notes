"""SQL language detector."""

from .base import ExtensionDetector, LanguageInfo

SQL_INFO = LanguageInfo(
    name="sql",
    category="backend",
    extensions=frozenset({".sql", ".mysql", ".pgsql"}),
)


class SqlDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(SQL_INFO)
