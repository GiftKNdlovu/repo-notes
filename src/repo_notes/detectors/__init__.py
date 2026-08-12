"""Language detectors package."""

from .base import LanguageInfo
from .registry import (
    C_CPP_INFO,
    DOCKER_INFO,
    GO_INFO,
    JAVA_INFO,
    JS_INFO,
    KOTLIN_INFO,
    PHP_INFO,
    PYTHON_INFO,
    R_LANG_INFO,
    RUBY_INFO,
    RUST_INFO,
    SHELL_INFO,
    SQL_INFO,
    SWIFT_INFO,
    TS_INFO,
    DetectorRegistry,
    get_registry,
)

__all__ = [
    "LanguageInfo",
    "DetectorRegistry",
    "get_registry",
    "PYTHON_INFO",
    "JS_INFO",
    "TS_INFO",
    "GO_INFO",
    "RUST_INFO",
    "JAVA_INFO",
    "C_CPP_INFO",
    "RUBY_INFO",
    "PHP_INFO",
    "SWIFT_INFO",
    "KOTLIN_INFO",
    "R_LANG_INFO",
    "SHELL_INFO",
    "SQL_INFO",
    "DOCKER_INFO",
]
