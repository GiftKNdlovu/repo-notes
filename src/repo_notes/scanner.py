"""File scanner with .gitignore support."""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import pathspec


DEFAULT_IGNORE = [
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    "*.egg-info/",
    ".git/",
    ".svn/",
    ".hg/",
    "node_modules/",
    ".venv/",
    "venv/",
    "virtualenv/",
    ".tox/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    "__pypackages__/",
    ".DS_Store",
    "Thumbs.db",
    ".idea/",
    ".vscode/",
    "*.swp",
    "*.swo",
    "*~",
]


@dataclass(frozen=True, slots=True)
class FileInfo:
    path: Path
    relative_path: Path
    size: int
    extension: str
    is_binary: bool


def build_spec(root: Path, extra_excludes: list[str] | None = None) -> pathspec.PathSpec:
    """Build PathSpec from .gitignore + defaults + extra excludes."""
    lines = list(DEFAULT_IGNORE)
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        with gitignore_path.open() as f:
            lines.extend(f.read().splitlines())
    if extra_excludes:
        lines.extend(extra_excludes)
    return pathspec.PathSpec.from_lines("gitignore", lines)


def is_binary(path: Path) -> bool:
    """Quick binary detection by reading first 8KB."""
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def scan_directory(
    root: Path,
    include_hidden: bool = False,
    extra_excludes: list[str] | None = None,
    min_file_size: int = 0,
) -> Iterator[FileInfo]:
    """Scan a directory and yield FileInfo for each non-ignored file.

    Args:
        root: Directory to scan
        include_hidden: Whether to include hidden files
        extra_excludes: Additional gitignore-style patterns to exclude
        min_file_size: Minimum file size in bytes (0 = no minimum)
    """
    root = root.resolve()
    spec = build_spec(root, extra_excludes)

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if spec.match_file(rel):
            continue
        if not include_hidden and any(part.startswith(".") for part in path.relative_to(root).parts):
            continue

        try:
            stat = path.stat()
            if min_file_size > 0 and stat.st_size < min_file_size:
                continue
            yield FileInfo(
                path=path,
                relative_path=path.relative_to(root),
                size=stat.st_size,
                extension=path.suffix.lower(),
                is_binary=is_binary(path),
            )
        except OSError:
            continue