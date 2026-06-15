"""Extractor for type coverage estimation."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text


# Languages always considered fully typed
FULLY_TYPED = {"go", "rust", "kotlin", "java", "swift", "scala"}
# Extensions for typed/untyped JS-family
TS_EXTS = {".ts", ".tsx"}
JS_EXTS = {".js", ".jsx"}


@dataclass(slots=True)
class TypeCoverageResult:
    typed_files: int = 0
    untyped_files: int = 0
    typed_lines: int = 0
    untyped_lines: int = 0
    by_extension: dict[str, dict[str, int]] = field(default_factory=dict)


class TypeCoverageExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> TypeCoverageResult:
        result = TypeCoverageResult()

        for f in files:
            if f.is_binary:
                continue
            ext = f.extension
            content = read_text(f.path)
            lines = len(content.splitlines()) if content else 0

            if ext not in result.by_extension:
                result.by_extension[ext] = {"files": 0, "typed_lines": 0, "untyped_lines": 0}
            result.by_extension[ext]["files"] += 1

            is_typed = self._is_typed(f, content)
            if is_typed:
                result.typed_files += 1
                result.typed_lines += lines
                result.by_extension[ext]["typed_lines"] += lines
            else:
                result.untyped_files += 1
                result.untyped_lines += lines
                result.by_extension[ext]["untyped_lines"] += lines

        return result

    def _is_typed(self, f: FileInfo, content: str) -> bool:
        ext = f.extension
        lang = f.relative_path.suffix.lower()

        if lang in (".py",):
            # Python: check for type hints in function signatures
            if re.search(r"def\s+\w+\s*\([^)]*:\s*\w+", content) or re.search(r"->\s*\w+", content):
                return True
            return False

        if lang in TS_EXTS:
            return True  # TypeScript is always typed
        if lang in JS_EXTS:
            return False  # Plain JS is untyped (ignore JSDoc for simplicity)

        # Use detector registry for language-based classification
        if lang:
            from repo_notes.detectors import get_registry
            info = get_registry().classify(f.path)
            if info and info.name in FULLY_TYPED:
                return True

        return False
