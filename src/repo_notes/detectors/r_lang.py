"""R language detector."""

from .base import ExtensionDetector, LanguageInfo

R_LANG_INFO = LanguageInfo(
    name="r",
    category="backend",
    extensions=frozenset({".r", ".rmd", ".rda", ".rds"}),
)


class RDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(R_LANG_INFO)
