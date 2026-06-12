"""Key files extractor (README, configs, entry points)."""

from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo


KEY_PATTERNS = {
    "readme": ["readme", "read_me"],
    "license": ["license", "licence", "copying"],
    "changelog": ["changelog", "changes", "history", "releases"],
    "contributing": ["contributing", "contribute"],
    "code_of_conduct": ["code_of_conduct", "conduct"],
    "config": [".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".json"],
    "docker": ["dockerfile", "docker-compose", ".dockerignore"],
    "ci": [".github/workflows", ".gitlab-ci", ".circleci", ".travis.yml", "azure-pipelines", "jenkinsfile"],
    "entrypoint": ["main.py", "app.py", "cli.py", "run.py", "server.py", "manage.py",
                    "index.js", "main.js", "app.js", "server.js",
                    "main.go", "cmd/main.go",
                    "main.rs", "src/main.rs",
                    "package.json", "pyproject.toml", "cargo.toml", "go.mod"],
}


@dataclass(slots=True)
class KeyFilesResult:
    categories: dict[str, list[Path]] = field(default_factory=dict)


class KeyFilesExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> KeyFilesResult:
        categories: dict[str, list[Path]] = {k: [] for k in KEY_PATTERNS}

        for f in files:
            rel = f.relative_path
            name_lower = rel.name.lower()
            path_str = rel.as_posix().lower()

            for cat, patterns in KEY_PATTERNS.items():
                if any(p in name_lower or p in path_str for p in patterns):
                    categories[cat].append(rel)
                    break

        return KeyFilesResult(categories={k: v for k, v in categories.items() if v})