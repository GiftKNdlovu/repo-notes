"""Extractor for TODO/FIXME/HACK and similar developer comments."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text

TODO_PATTERNS = [
    (r"(?i)TODO\b:?\s*(.*)", "TODO"),
    (r"(?i)FIXME\b:?\s*(.*)", "FIXME"),
    (r"(?i)HACK\b:?\s*(.*)", "HACK"),
    (r"(?i)XXX\b:?\s*(.*)", "XXX"),
    (r"(?i)BUG\b:?\s*(.*)", "BUG"),
    (r"(?i)WORKAROUND\b:?\s*(.*)", "WORKAROUND"),
    (r"(?i)HACKME\b:?\s*(.*)", "HACKME"),
]

MAX_PER_TAG = 30


@dataclass(slots=True)
class TodosResult:
    items: list[dict] = field(default_factory=list)
    count_by_tag: dict[str, int] = field(default_factory=dict)


class TodosExtractor:
    def __init__(self):
        self._compiled = [(re.compile(p), tag) for p, tag in TODO_PATTERNS]

    def extract(self, root: Path, files: list[FileInfo]) -> TodosResult:
        items: list[dict] = []
        counts: dict[str, int] = {}

        for f in files:
            if f.is_binary:
                continue
            content = read_text(f.path)
            if not content:
                continue
            rel = f.relative_path.as_posix()
            for pattern, tag in self._compiled:
                for match in pattern.finditer(content):
                    line_no = content[:match.start()].count("\n") + 1
                    message = match.group(1).strip() if match.lastindex else ""
                    items.append({
                        "file": rel,
                        "tag": tag,
                        "line": line_no,
                        "message": message[:120],
                    })
                    counts[tag] = counts.get(tag, 0) + 1

        # Limit per tag, keep highest line numbers as a heuristic
        items.sort(key=lambda x: x["line"], reverse=True)
        limited = []
        tag_seen: dict[str, int] = {}
        for item in items:
            tag_seen[item["tag"]] = tag_seen.get(item["tag"], 0) + 1
            if tag_seen[item["tag"]] <= MAX_PER_TAG:
                limited.append(item)
        limited.sort(key=lambda x: (x["file"], x["line"]))

        return TodosResult(items=limited, count_by_tag=counts)
