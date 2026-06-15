"""Rust language detector."""

from .base import ExtensionDetector, LanguageInfo

RUST_INFO = LanguageInfo(
    name="rust",
    category="backend",
    extensions=frozenset({".rs"}),
)


class RustDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(RUST_INFO)
