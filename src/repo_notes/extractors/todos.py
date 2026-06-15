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


COMMENT_EXTENSIONS: dict[str, frozenset[str]] = {
    "#": frozenset({".py", ".pyi", ".pyx", ".rb", ".rhtml", ".erb",
                    ".sh", ".bash", ".zsh", ".ksh", ".csh",
                    ".yaml", ".yml", ".toml",
                    ".r", ".rmd", ".pl", ".pm", ".el", ".clj", ".cljs",
                    ".conf", ".cfg", ".desktop", ".service"}),
    "//": frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".cts", ".mts",
                     ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx", ".hxx",
                     ".java", ".go", ".rs", ".swift", ".kt", ".kts",
                     ".php", ".cs", ".fs", ".dart", ".scala",
                     ".groovy", ".gradle", ".vue", ".svelte"}),
    "--": frozenset({".sql", ".lua", ".hs", ".lhs"}),
    "<!--": frozenset({".html", ".htm", ".xhtml", ".xml", ".svg", ".xslt", ".xsd"}),
    "%": frozenset({".tex", ".cls", ".sty"}),
}

COMMENT_FILENAMES: dict[str, frozenset[str]] = {
    "#": frozenset({"dockerfile", "containerfile", "makefile", "gemfile",
                    "rakefile", "procfile",
                    "gitignore", "gitattributes", "editorconfig",
                    "env", "python-version", "nvmrc", "node-version",
                    "tool-versions", "pre-commit-config.yaml",
                    "requirements.txt", "pipfile", "pipfile.lock",
                    "gemfile.lock", "gemfile.lock",
                    ".bashrc", ".zshrc", ".profile", ".aliases"}),
    "//": frozenset({"eslintrc.js", "eslintrc.cjs", "prettierrc.js",
                     "babel.config.js", "babel.config.cjs",
                     "webpack.config.js", "vite.config.js",
                     "rollup.config.js", "postcss.config.js"}),
}

MAX_PER_TAG = 30


@dataclass(slots=True)
class TodosResult:
    items: list[dict] = field(default_factory=list)
    count_by_tag: dict[str, int] = field(default_factory=dict)


class TodosExtractor:
    def __init__(self):
        self._compiled = [(re.compile(p), tag) for p, tag in TODO_PATTERNS]
        self._ext_comment: dict[str, str | None] = {}
        self._name_comment: dict[str, str | None] = {}

    def _get_prefix(self, f: FileInfo) -> str | None:
        ext = f.relative_path.suffix.lower()
        if ext not in self._ext_comment:
            for prefix, extensions in COMMENT_EXTENSIONS.items():
                if ext in extensions:
                    self._ext_comment[ext] = prefix
                    break
            else:
                self._ext_comment[ext] = None
        cached_ext = self._ext_comment.get(ext)
        if cached_ext:
            return cached_ext

        name = f.relative_path.name.lower()
        if name not in self._name_comment:
            for prefix, names in COMMENT_FILENAMES.items():
                if name in names or any(name.startswith(n) for n in names):
                    self._name_comment[name] = prefix
                    break
            else:
                self._name_comment[name] = None
        return self._name_comment.get(name)

    def _is_in_comment(self, line_before: str, line_after: str, prefix: str) -> bool:
        if prefix == "//":
            if self._marker_outside_string(line_before, "//"):
                return True
            if self._marker_outside_string(line_before, "/*"):
                return True
            if line_before.lstrip().startswith("*"):
                return True
            return False
        if prefix == "<!--":
            return "<!--" in line_before
        if prefix == "--":
            return self._marker_outside_string(line_before, "--")
        return self._marker_outside_string(line_before, prefix)

    @staticmethod
    def _marker_outside_string(text: str, marker: str) -> bool:
        """Check if marker appears in text and is not inside a string literal."""
        idx = text.find(marker)
        if idx < 0:
            return False
        in_single = False
        in_double = False
        i = 0
        while i < idx:
            c = text[i]
            if c == "\\":
                i += 2
                continue
            if c == "'" and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            i += 1
        return not (in_single or in_double)

    def extract(self, root: Path, files: list[FileInfo]) -> TodosResult:
        items: list[dict] = []
        counts: dict[str, int] = {}

        for f in files:
            if f.is_binary:
                continue
            prefix = self._get_prefix(f)
            if not prefix:
                continue
            content = read_text(f.path)
            if not content:
                continue
            rel = f.relative_path.as_posix()
            for pattern, tag in self._compiled:
                for match in pattern.finditer(content):
                    line_no = content[:match.start()].count("\n") + 1
                    line_start = content.rfind("\n", 0, match.start()) + 1
                    line_end = content.find("\n", match.end())
                    if line_end == -1:
                        line_end = len(content)
                    line_before = content[line_start:match.start()]
                    line_after = content[match.end() : line_end]
                    if not self._is_in_comment(line_before, line_after, prefix):
                        continue
                    message = match.group(1).strip() if match.lastindex else ""
                    items.append({
                        "file": rel,
                        "tag": tag,
                        "line": line_no,
                        "message": message[:120],
                    })
                    counts[tag] = counts.get(tag, 0) + 1

        items.sort(key=lambda x: x["line"], reverse=True)
        limited = []
        tag_seen: dict[str, int] = {}
        for item in items:
            tag_seen[item["tag"]] = tag_seen.get(item["tag"], 0) + 1
            if tag_seen[item["tag"]] <= MAX_PER_TAG:
                limited.append(item)
        limited.sort(key=lambda x: (x["file"], x["line"]))

        return TodosResult(items=limited, count_by_tag=counts)
