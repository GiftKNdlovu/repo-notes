"""Ruby language detector."""

from .base import ExtensionDetector, LanguageInfo

RUBY_INFO = LanguageInfo(
    name="ruby",
    category="backend",
    extensions=frozenset({".rb", ".erb", ".rake", ".gemspec"}),
)


class RubyDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(RUBY_INFO)
