"""Code statistics extractor."""

from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.detectors import get_registry


@dataclass(slots=True)
class StatsResult:
    total_files: int
    total_lines: int
    total_size: int
    by_language: dict[str, dict[str, int]] = field(default_factory=dict)
    largest_files: list[tuple[Path, int]] = field(default_factory=list)


class StatsExtractor:
    def __init__(self, top_n: int = 10):
        self.top_n = top_n
        self._registry = get_registry()

    def extract(self, root: Path, files: list[FileInfo]) -> StatsResult:
        by_lang: dict[str, dict[str, int]] = {}
        total_lines = 0
        total_size = 0
        file_sizes: list[tuple[Path, int]] = []

        for f in files:
            if f.is_binary:
                continue

            lang_info = self._registry.classify(f.path)
            lang = lang_info.name if lang_info else "unknown"

            lines = self._count_lines(f.path)
            total_lines += lines
            total_size += f.size
            file_sizes.append((f.relative_path, lines))

            if lang not in by_lang:
                by_lang[lang] = {"files": 0, "lines": 0, "size": 0}
            by_lang[lang]["files"] += 1
            by_lang[lang]["lines"] += lines
            by_lang[lang]["size"] += f.size

        largest = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:self.top_n]

        return StatsResult(
            total_files=len(files),
            total_lines=total_lines,
            total_size=total_size,
            by_language=by_lang,
            largest_files=largest,
        )

    def _count_lines(self, path: Path) -> int:
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                return sum(1 for _ in f)
        except OSError:
            return 0