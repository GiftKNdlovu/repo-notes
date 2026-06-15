"""Readme metadata extractor."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class ReadmeData:
    name: str = ""
    version: str = ""
    description: str = ""
    license_type: str = ""
    python_requires: str = ""
    install_cmd: str = ""
    dev_install_cmd: str = ""
    runtime_deps: list[str] = field(default_factory=list)
    dev_deps: list[str] = field(default_factory=list)
    has_tests: bool = False
    has_ci: bool = False
    has_docker: bool = False
    ci_provider: str = ""


class ReadmeDataExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> ReadmeData:
        data = ReadmeData()
        for f in files:
            if f.is_binary:
                continue
            name = f.relative_path.name
            if name == "pyproject.toml":
                self._parse_pyproject(f.path, data)
            elif name == "package.json":
                self._parse_package_json(f.path, data)
            elif name == "Cargo.toml":
                self._parse_cargo_toml(f.path, data)
            elif name == "go.mod":
                self._parse_go_mod(f.path, data)
            elif name in ("LICENSE", "LICENSE.txt", "LICENSE.md"):
                data.license_type = self._detect_license(f.path)
            elif name == "requirements.txt":
                if not data.name:
                    data.name = root.name
                if not data.install_cmd:
                    data.install_cmd = "pip install -r requirements.txt"
            elif name == "Makefile":
                data.has_tests = True
            elif f.relative_path.match(".github/workflows/*.yml"):
                data.has_ci = True
                data.ci_provider = "GitHub Actions"
            elif f.relative_path.match(".gitlab-ci.yml"):
                data.has_ci = True
                data.ci_provider = "GitLab CI"
            elif name in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml"):
                data.has_docker = True

        for f in files:
            if f.is_binary:
                continue
            rel = f.relative_path
            parts = rel.parts
            if "tests" in parts or "test" in parts or "spec" in parts:
                data.has_tests = True

        if not data.name:
            data.name = root.name
        if not data.install_cmd:
            if data.runtime_deps or data.name == root.name:
                data.install_cmd = f"pip install {data.name}" if data.name != root.name else "pip install ."
        if not data.dev_install_cmd:
            data.dev_install_cmd = "pip install -e \".[dev]\""

        return data

    def _parse_pyproject(self, path: Path, data: ReadmeData) -> None:
        try:
            with path.open("rb") as f:
                raw = tomllib.load(f)
            project = raw.get("project", {})
            if not data.name:
                data.name = project.get("name", "")
            if not data.version:
                data.version = project.get("version", "")
            if not data.description:
                data.description = project.get("description", "")
            if not data.python_requires:
                data.python_requires = project.get("requires-python", "")
            deps = project.get("dependencies", [])
            if deps:
                data.runtime_deps = [d.split(">")[0].split(">=")[0].split("~=")[0].split("!=")[0].strip() for d in deps]
            opt_deps = project.get("optional-dependencies", {})
            if opt_deps:
                for group, pkgs in opt_deps.items():
                    data.dev_deps.extend(
                        p.split(">")[0].split(">=")[0].split("~=")[0].split("!=")[0].strip()
                        for p in pkgs
                    )
            if not data.install_cmd:
                data.install_cmd = f"pip install {data.name}" if data.name else ""
        except Exception:
            pass

    def _parse_package_json(self, path: Path, data: ReadmeData) -> None:
        try:
            with path.open() as f:
                raw = json.load(f)
            if not data.name:
                data.name = raw.get("name", "")
            if not data.version:
                data.version = raw.get("version", "")
            if not data.description:
                data.description = raw.get("description", "")
            deps = raw.get("dependencies", {})
            if deps:
                data.runtime_deps = list(deps.keys())
            dev_deps = raw.get("devDependencies", {})
            if dev_deps:
                data.dev_deps.extend(dev_deps.keys())
            if not data.install_cmd:
                data.install_cmd = "npm install"
            if not data.dev_install_cmd:
                data.dev_install_cmd = "npm install --dev"
        except Exception:
            pass

    def _parse_cargo_toml(self, path: Path, data: ReadmeData) -> None:
        try:
            with path.open("rb") as f:
                raw = tomllib.load(f)
            pkg = raw.get("package", {})
            if not data.name:
                data.name = pkg.get("name", "")
            if not data.version:
                data.version = pkg.get("version", "")
            if not data.description:
                data.description = pkg.get("description", "")
            deps = raw.get("dependencies", {})
            if deps:
                data.runtime_deps = list(deps.keys())
            dev_deps = raw.get("dev-dependencies", {})
            if dev_deps:
                data.dev_deps.extend(dev_deps.keys())
            if not data.install_cmd:
                data.install_cmd = "cargo install"
            if not data.dev_install_cmd:
                data.dev_install_cmd = "cargo build"
        except Exception:
            pass

    def _parse_go_mod(self, path: Path, data: ReadmeData) -> None:
        try:
            with path.open() as f:
                for line in f:
                    if line.startswith("module ") and not data.name:
                        data.name = line.split(" ", 1)[1].strip()
                        break
            if not data.install_cmd:
                data.install_cmd = "go install ."
            if not data.dev_install_cmd:
                data.dev_install_cmd = "go mod download"
        except Exception:
            pass

    def _detect_license(self, path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            text_lower = text.lower()
            if "mit" in text_lower and "permission is hereby granted" in text_lower:
                return "MIT"
            if "apache" in text_lower and "version 2.0" in text_lower:
                return "Apache-2.0"
            if "gnu" in text_lower and "general public" in text_lower:
                if "version 3" in text_lower or "gpl-3" in text_lower:
                    return "GPL-3.0"
                if "version 2" in text_lower or "gpl-2" in text_lower:
                    return "GPL-2.0"
            if "bsd" in text_lower:
                return "BSD"
            if "unlicense" in text_lower:
                return "Unlicense"
            return "Other"
        except Exception:
            return ""
