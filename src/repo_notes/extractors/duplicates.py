"""Extractor for detecting duplicate or near-duplicate files."""

import hashlib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class DuplicateResult:
    duplicates: list[dict] = field(default_factory=list)
    total_duplicates: int = 0
    total_saved_bytes: int = 0


class DuplicateExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> DuplicateResult:
        # Group files by size for fast candidate filtering
        by_size: dict[int, list[FileInfo]] = defaultdict(list)
        for f in files:
            if f.is_binary:
                continue
            by_size[f.size].append(f)

        duplicates: list[dict] = []
        total_saved = 0

        for size, group in by_size.items():
            if len(group) < 2:
                continue
            # Hash each file's content for exact comparison
            hash_map: dict[str, list[Path]] = defaultdict(list)
            for f in group:
                h = self._file_hash(f.path)
                if h:
                    hash_map[h].append(f.relative_path)

            for hash_val, paths in hash_map.items():
                if len(paths) >= 2:
                    target = paths[0]
                    for dup in paths[1:]:
                        duplicates.append({
                            "file": dup.as_posix(),
                            "duplicate_of": target.as_posix(),
                            "size": size,
                            "similarity": 1.0,
                        })
                        total_saved += size

        duplicates.sort(key=lambda x: x["size"], reverse=True)

        return DuplicateResult(
            duplicates=duplicates,
            total_duplicates=len(duplicates),
            total_saved_bytes=total_saved,
        )

    def _file_hash(self, path: Path) -> str | None:
        try:
            h = hashlib.sha256()
            with path.open("rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return None
