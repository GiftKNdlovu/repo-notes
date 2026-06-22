"""C/C++ language detector."""

from .base import ExtensionDetector, LanguageInfo

C_CPP_INFO = LanguageInfo(
    name="c_cpp",
    category="backend",
    extensions=frozenset({".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hh", ".hxx"}),
)


class CppDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(C_CPP_INFO)
