"""Python language detector."""

from .base import ExtensionDetector, LanguageInfo

PYTHON_INFO = LanguageInfo(
    name="python",
    category="backend",
    extensions=frozenset({".py", ".pyi", ".pyx", ".pxd", ".pxi", ".ipynb"}),
)


class PythonDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(PYTHON_INFO)
