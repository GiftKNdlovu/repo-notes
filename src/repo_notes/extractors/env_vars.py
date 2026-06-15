"""Extractor for environment variables consumed by the project."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from repo_notes.file_cache import read_text
from repo_notes.scanner import FileInfo

ENV_PATTERNS = [
    # Python: os.getenv("VAR"), os.environ.get("VAR"), os.environ["VAR"]
    (r"""os\.getenv\(['\"]([^'\"]+)['\"]""", "Python"),
    (r"""os\.environ\.(?:get|__getitem__)\s*\(\s*['\"]([^'\"]+)['\"]""", "Python"),
    # JavaScript/TypeScript: process.env.VAR, process.env["VAR"]
    (r"""process\.env\.([A-Za-z_][A-Za-z0-9_]*)""", "JavaScript"),
    (r"""process\.env\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]""", "JavaScript"),
    # Rust: env!("VAR")
    (r"""env!\s*\(\s*['\"]([^'\"]+)['\"]""", "Rust"),
    # Shell: $VAR, ${VAR}
    (r"""\$\{?([A-Z_][A-Z0-9_]+)\}?""", "Shell"),
    # Generic getenv function calls
    (r"""getenv\s*\(\s*['\"]([^'\"]+)['\"]""", "Generic"),
]


@dataclass(slots=True)
class EnvVarsResult:
    variables: dict[str, list[str]] = field(default_factory=dict)


class EnvVarsExtractor:
    def __init__(self):
        self._compiled = [(re.compile(p), lang) for p, lang in ENV_PATTERNS]

    def extract(self, root: Path, files: list[FileInfo]) -> EnvVarsResult:
        var_map: dict[str, set[str]] = {}

        for f in files:
            if f.is_binary:
                continue
            content = read_text(f.path)
            if not content:
                continue
            rel = f.relative_path.as_posix()
            for pattern, _lang in self._compiled:
                for match in pattern.finditer(content):
                    var_name = match.group(1)
                    if var_name not in var_map:
                        var_map[var_name] = set()
                    var_map[var_name].add(rel)

        return EnvVarsResult(
            variables={k: sorted(v) for k, v in sorted(var_map.items())}
        )
