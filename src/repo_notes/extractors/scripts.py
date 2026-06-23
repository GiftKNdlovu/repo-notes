"""Extractor for build scripts (package.json, Makefile, justfile)."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python < 3.11
    import tomli as tomllib

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class ScriptsResult:
    package_json: dict[str, str] = field(default_factory=dict)
    makefile_targets: list[str] = field(default_factory=list)
    justfile_recipes: list[str] = field(default_factory=list)
    pyproject_scripts: dict[str, str] = field(default_factory=dict)


class ScriptsExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> ScriptsResult:
        result = ScriptsResult()

        for f in files:
            name = f.relative_path.name
            if name == "package.json":
                result.package_json = self._parse_package_json(f.path)
            elif name == "Makefile":
                result.makefile_targets = self._parse_makefile(f.path)
            elif name == "justfile":
                result.justfile_recipes = self._parse_justfile(f.path)

        # Also check pyproject.toml for tool scripts
        for f in files:
            if f.relative_path.name == "pyproject.toml":
                result.pyproject_scripts = self._parse_pyproject_scripts(f.path)

        return result

    def _parse_package_json(self, path: Path) -> dict[str, str]:
        try:
            with path.open() as f:
                data = json.load(f)
            return data.get("scripts", {})
        except Exception:
            return {}

    def _parse_makefile(self, path: Path) -> list[str]:
        targets = []
        try:
            with path.open() as f:
                for line in f:
                    m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_.\-]*)\s*:", line)
                    if m:
                        t = m.group(1)
                        if t not in (".PHONY", ".DEFAULT", ".SILENT", ".EXPORT_ALL_VARIABLES"):
                            targets.append(t)
        except OSError:
            pass
        return targets

    def _parse_justfile(self, path: Path) -> list[str]:
        recipes = []
        try:
            with path.open() as f:
                for line in f:
                    m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_\-]*)\s*:", line)
                    if m:
                        recipes.append(m.group(1))
        except OSError:
            pass
        return recipes

    def _parse_pyproject_scripts(self, path: Path) -> dict[str, str]:
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
            result = {}
            for section in ("scripts", "gui-scripts"):
                if "project" in data and section in data["project"]:
                    result.update(data["project"][section])
            if "tool" in data:
                for tool_name in ("hatch", "poetry", "flit"):
                    if tool_name in data["tool"] and "scripts" in data["tool"][tool_name]:
                        result.update(data["tool"][tool_name]["scripts"])
            return result
        except Exception:
            return {}
