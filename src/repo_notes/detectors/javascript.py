"""JavaScript/TypeScript language detector."""

from .base import ExtensionDetector, LanguageInfo

JS_INFO = LanguageInfo(
    name="javascript",
    category="frontend",
    extensions=frozenset({".js", ".jsx", ".mjs", ".cjs"}),
)

TS_INFO = LanguageInfo(
    name="typescript",
    category="frontend",
    extensions=frozenset({".ts", ".tsx", ".mts", ".cts"}),
)


class JavaScriptDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(JS_INFO)


class TypeScriptDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(TS_INFO)
