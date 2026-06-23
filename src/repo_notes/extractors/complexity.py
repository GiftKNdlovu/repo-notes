"""Extractor for code complexity estimation."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from repo_notes.file_cache import read_text
from repo_notes.scanner import FileInfo

COMPLEXITY_THRESHOLD = 10  # minimum function length to flag
MAX_NESTING_WARN = 4       # nesting depth beyond this is flagged


@dataclass(slots=True)
class ComplexityResult:
    complex_files: list[dict] = field(default_factory=list)
    avg_function_length: float = 0.0
    max_nesting: int = 0


class ComplexityExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> ComplexityResult:
        all_fn_lengths: list[int] = []
        complex_files: list[dict] = []
        global_max_nesting = 0

        for f in files:
            if f.is_binary:
                continue
            content = read_text(f.path)
            if not content:
                continue

            fn_lengths = self._function_lengths(content)
            all_fn_lengths.extend(fn_lengths)
            max_nest = self._max_nesting(content, extension=f.extension)
            global_max_nesting = max(global_max_nesting, max_nest)

            flagged = []
            for length in fn_lengths:
                if length > COMPLEXITY_THRESHOLD:
                    flagged.append(length)
            if flagged or max_nest > MAX_NESTING_WARN:
                complex_files.append({
                    "file": f.relative_path.as_posix(),
                    "long_functions": flagged,
                    "max_nesting": max_nest,
                    "score": sum(flagged) + max_nest * 2,
                })

        complex_files.sort(key=lambda x: x["score"], reverse=True)
        avg = sum(all_fn_lengths) / len(all_fn_lengths) if all_fn_lengths else 0.0

        return ComplexityResult(
            complex_files=complex_files[:20],
            avg_function_length=round(avg, 1),
            max_nesting=global_max_nesting,
        )

    def _function_lengths(self, content: str) -> list[int]:
        lines = content.split("\n")
        in_fn = False
        fn_start = 0
        brace_depth = 0
        lengths = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            # Detect function/method definition
            if re.match(
                r"^\s*(?:def\s+\w+|function\s*\w*|async\s+function\s*\w*|"
                r"\w+\s*=\s*(?:def|lambda|function)|"
                r"fn\s+\w+|func\s+\w+|defn\s+\w+)",
                stripped,
            ):
                if in_fn:
                    lengths.append(i - fn_start)
                fn_start = i
                in_fn = True
                brace_depth = 0

            if in_fn:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0 and "{" in content:
                    # C-style brace tracking
                    pass

        if in_fn:
            lengths.append(len(lines) - fn_start)

        return [ln for ln in lengths if ln > 1]

    def _max_nesting(self, content: str, extension: str = "") -> int:
        is_python = extension in (".py", ".pyw", ".pyx")
        if not is_python and not extension:
            is_python = self._looks_like_python(content)
        if is_python:
            return self._python_nesting(content)
        return self._brace_nesting(content)

    @staticmethod
    def _looks_like_python(content: str) -> bool:
        for line in content.split("\n"):
            stripped = line.strip()
            if re.match(r"^\s*(?:def\s+|class\s+|elif\s+|except\s+|finally\s+)", stripped):
                return True
        return False

    def _python_nesting(self, content: str) -> int:
        max_depth = 0
        block_indents: list[int] = []
        comment_prefixes = ("#", '"""', "'''", "//", "/*", "*", '"', "'")

        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(comment_prefixes):
                continue

            leading = len(line) - len(line.lstrip())

            while block_indents and block_indents[-1] >= leading:
                block_indents.pop()

            if re.match(
                r"^\s*(?:if|for|while|with|try|except|def|class|elif|else|finally)\b",
                stripped,
            ):
                if not block_indents or leading > block_indents[-1]:
                    block_indents.append(leading)

            max_depth = max(max_depth, len(block_indents))

        return max_depth

    def _brace_nesting(self, content: str) -> int:
        max_depth = 0
        depth = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "//", "/*", "*", '"', "'")):
                continue
            opens = stripped.count("{") + stripped.count("(") + stripped.count("[")
            closes = stripped.count("}") + stripped.count(")") + stripped.count("]")
            depth += opens - closes
            depth = max(depth, 0)
            max_depth = max(max_depth, depth)
        return max_depth
