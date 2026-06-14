"""Shared file content cache to avoid redundant reads across extractors."""

from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def clear_cache() -> None:
    read_text.cache_clear()
