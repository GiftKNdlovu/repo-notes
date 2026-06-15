"""Incremental cache to skip re-scanning unchanged projects.

Persists file metadata (mtime, size, content hash) in .repo-notes-cache.json.
On subsequent runs, if no files changed and no config changed, skip the scan.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from repo_notes.config import Config
from repo_notes.scanner import FileInfo, scan_directory

CACHE_VERSION = 1
CACHE_FILENAME = ".repo-notes-cache.json"


@dataclass(frozen=True)
class FileState:
    mtime: float
    size: int
    hash: str  # sha256 hex digest


def _content_hash(path: Path) -> str:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def _config_hash(cfg: Config) -> str:
    h = hashlib.sha256()
    h.update(str(cfg.include_hidden).encode())
    h.update(str(cfg.min_file_size).encode())
    for pat in sorted(cfg.exclude_patterns):
        h.update(pat.encode())
    for name in sorted(cfg.detectors.enabled):
        h.update(name.encode())
    ext = cfg.extractors
    h.update("".join([
        str(ext.structure), str(ext.key_files), str(ext.stats),
        str(ext.dependencies), str(ext.git), str(ext.architecture),
        str(ext.security),
    ]).encode())
    h.update(str(cfg.security.entropy_threshold).encode())
    h.update(str(cfg.structure.max_depth).encode())
    return h.hexdigest()


class CacheManager:
    """Manages the incremental scan cache (.repo-notes-cache.json)."""

    def __init__(self, root: Path, cfg: Config):
        self.root = root.resolve()
        self.cache_path = self.root / CACHE_FILENAME
        self.cfg = cfg
        self._data: Optional[dict] = None

    def load(self) -> dict:
        if self._data is not None:
            return self._data
        try:
            raw = self.cache_path.read_text(encoding="utf-8")
            self._data = json.loads(raw)
            if self._data.get("version") != CACHE_VERSION:
                self._data = {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._data = {}
        return self._data

    def save(self, file_states: Dict[str, FileState]) -> None:
        data = {
            "version": CACHE_VERSION,
            "config_hash": _config_hash(self.cfg),
            "files": {
                path: {
                    "mtime": fs.mtime,
                    "size": fs.size,
                    "hash": fs.hash,
                }
                for path, fs in sorted(file_states.items())
            },
        }
        tmp = self.cache_path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
            tmp.replace(self.cache_path)
        except OSError:
            pass  # cache write failures are non-fatal

    def is_valid(self) -> bool:
        data = self.load()
        if not data:
            return False
        if data.get("config_hash") != _config_hash(self.cfg):
            return False
        return True

    def compute_current_states(self) -> Dict[str, FileState]:
        states: Dict[str, FileState] = {}
        for fi in scan_directory(
            self.root,
            include_hidden=self.cfg.include_hidden,
            extra_excludes=self.cfg.exclude_patterns,
            min_file_size=self.cfg.min_file_size,
        ):
            key = fi.relative_path.as_posix()
            try:
                stat = fi.path.stat()
                states[key] = FileState(
                    mtime=stat.st_mtime_ns,
                    size=stat.st_size,
                    hash=_content_hash(fi.path),
                )
            except OSError:
                continue
        return states

    def has_changes(self, current: Dict[str, FileState]) -> bool:
        cached = self.load().get("files", {})
        if set(current.keys()) != set(cached.keys()):
            return True
        for key, fs in current.items():
            entry = cached.get(key)
            if entry is None:
                return True
            if entry["mtime"] != fs.mtime or entry["size"] != fs.size:
                return True
        return False

    def save_from_file_infos(self, files: list[FileInfo]) -> None:
        states: Dict[str, FileState] = {}
        for fi in files:
            key = fi.relative_path.as_posix()
            try:
                stat = fi.path.stat()
                states[key] = FileState(
                    mtime=stat.st_mtime_ns,
                    size=stat.st_size,
                    hash=_content_hash(fi.path),
                )
            except OSError:
                continue
        self.save(states)

    def clear(self) -> None:
        self._data = None
        try:
            self.cache_path.unlink()
        except FileNotFoundError:
            pass
