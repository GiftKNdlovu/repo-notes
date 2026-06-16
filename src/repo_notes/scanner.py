"""File scanner with .gitignore support."""

import os
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

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
    ".repo-notes-cache.json",
    ".repo-notes-cache.tmp",
    "REPO_NOTES.md",
    "REPO_NOTES_AGENTS.md",
    "REPO_NOTES.html",
    "REPO_NOTES.json",
    "rnREADME.md",
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


def _walk_entries(
    root: Path,
    include_hidden: bool = False,
) -> Iterator[os.DirEntry]:
    """Walk directory tree with os.scandir for zero-stat traversal."""
    stack: list[tuple[Path, bool]] = [(root, False)]
    while stack:
        dir_path, skip = stack.pop()
        if skip:
            continue
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    if not include_hidden and entry.name.startswith("."):
                        continue
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append((entry.path, False))
                        elif entry.is_file(follow_symlinks=False):
                            yield entry
                    except OSError:
                        continue
        except PermissionError:
            continue


def _process_entry(
    entry: os.DirEntry, root: Path, root_str: str, spec: pathspec.PathSpec,
    min_file_size: int,
) -> FileInfo | None:
    """Process a single DirEntry into FileInfo, or None if filtered out."""
    try:
        rel = entry.path[len(root_str):]
    except (ValueError, IndexError):
        return None
    if spec.match_file(rel):
        return None
    try:
        size = entry.stat().st_size
    except OSError:
        return None
    if min_file_size > 0 and size < min_file_size:
        return None
    path = Path(entry.path)
    try:
        binary = is_binary(path)
    except OSError:
        binary = True
    _, ext = os.path.splitext(entry.name)
    return FileInfo(
        path=path,
        relative_path=Path(rel),
        size=size,
        extension=ext.lower(),
        is_binary=binary,
    )


def scan_directory(
    root: Path,
    include_hidden: bool = False,
    extra_excludes: list[str] | None = None,
    min_file_size: int = 0,
) -> Iterator[FileInfo]:
    """Scan a directory and yield FileInfo for each non-ignored file.

    Uses os.scandir for fast directory traversal with cached stat info,
    and parallel binary detection via ThreadPoolExecutor.

    Args:
        root: Directory to scan
        include_hidden: Whether to include hidden files
        extra_excludes: Additional gitignore-style patterns to exclude
        min_file_size: Minimum file size in bytes (0 = no minimum)
    """
    root = root.resolve()
    spec = build_spec(root, extra_excludes)
    root_str = str(root) + "/"

    # Phase 1: walk tree and collect entry handles (fast, no I/O beyond stat)
    entries: list[os.DirEntry] = list(_walk_entries(root, include_hidden))

    if not entries:
        return

    # Phase 2: process all entries in parallel (gitignore matching + stat
    # caching + binary detection)
    max_workers = min(8, (os.cpu_count() or 1) * 2) if len(entries) > 1 else 1
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(_process_entry, e, root, root_str, spec, min_file_size)
            for e in entries
        ]
        for future in futures:
            result = future.result()
            if result is not None:
                yield result
