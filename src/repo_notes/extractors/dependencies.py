"""Dependencies extractor."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    import tomli as tomllib

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class DependenciesResult:
    python: dict[str, Any] = field(default_factory=dict)
    javascript: dict[str, Any] = field(default_factory=dict)
    go: dict[str, Any] = field(default_factory=dict)
    rust: dict[str, Any] = field(default_factory=dict)


class DependenciesExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> DependenciesResult:
        result = DependenciesResult()

        for f in files:
            rel = f.relative_path
            name = rel.name

            if name in ("requirements.txt", "requirements-dev.txt", "requirements-test.txt"):
                result.python[name] = self._parse_requirements(f.path)
            elif name == "pyproject.toml":
                result.python["pyproject.toml"] = self._parse_pyproject(f.path)
            elif name == "setup.py":
                result.python["setup.py"] = "present"
            elif name == "setup.cfg":
                result.python["setup.cfg"] = "present"
            elif name == "package.json":
                result.javascript["package.json"] = self._parse_package_json(f.path)
            elif name in ("pnpm-lock.yaml", "yarn.lock", "package-lock.json"):
                result.javascript[name] = "lockfile"
            elif name == "go.mod":
                result.go["go.mod"] = self._parse_go_mod(f.path)
            elif name == "go.sum":
                result.go["go.sum"] = "checksums"
            elif name == "Cargo.toml":
                result.rust["Cargo.toml"] = self._parse_cargo_toml(f.path)
            elif name == "Cargo.lock":
                result.rust["Cargo.lock"] = "lockfile"

        return result

    def _parse_requirements(self, path: Path) -> list[str]:
        try:
            with path.open() as f:
                return [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except OSError:
            return []

    def _parse_pyproject(self, path: Path) -> dict:
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            deps = {}
            if "project" in data and "dependencies" in data["project"]:
                deps["dependencies"] = data["project"]["dependencies"]
            if "project" in data and "optional-dependencies" in data["project"]:
                deps["optional"] = data["project"]["optional-dependencies"]
            if "tool" in data and "poetry" in data["tool"] and "dependencies" in data["tool"]["poetry"]:
                deps["poetry"] = data["tool"]["poetry"]["dependencies"]
            return deps
        except Exception:
            return {}

    def _parse_package_json(self, path: Path) -> dict:
        try:
            with path.open() as f:
                data = json.load(f)
            return {
                "dependencies": data.get("dependencies", {}),
                "devDependencies": data.get("devDependencies", {}),
                "peerDependencies": data.get("peerDependencies", {}),
            }
        except Exception:
            return {}

    def _parse_go_mod(self, path: Path) -> dict:
        try:
            with path.open() as f:
                lines = f.read().splitlines()
            deps = []
            in_require = False
            for line in lines:
                line = line.strip()
                if line.startswith("require ("):
                    in_require = True
                    continue
                if in_require and line == ")":
                    break
                if in_require and line:
                    deps.append(line)
            return {"requires": deps}
        except Exception:
            return {}

    def _parse_cargo_toml(self, path: Path) -> dict:
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            deps = {}
            if "dependencies" in data:
                deps["dependencies"] = data["dependencies"]
            if "dev-dependencies" in data:
                deps["dev-dependencies"] = data["dev-dependencies"]
            return deps
        except Exception:
            return {}
