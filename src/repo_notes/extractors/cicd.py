"""Extractor for CI/CD configuration files."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class CicdResult:
    github_actions: list[dict] = field(default_factory=list)
    gitlab_ci: list[dict] = field(default_factory=list)
    circleci: list[dict] = field(default_factory=list)
    jenkins_stages: list[str] = field(default_factory=list)


class CicdExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> CicdResult:
        result = CicdResult()
        for f in files:
            rel = f.relative_path.as_posix()
            name = f.relative_path.name
            if rel.startswith(".github/workflows/") and name.endswith((".yml", ".yaml")):
                wf = self._parse_github_workflow(f.path)
                if wf:
                    result.github_actions.append(wf)
            elif rel == ".gitlab-ci.yml":
                result.gitlab_ci = self._parse_gitlab_ci(f.path)
            elif rel == ".circleci/config.yml":
                result.circleci = self._parse_circleci(f.path)
            elif name == "Jenkinsfile":
                result.jenkins_stages = self._parse_jenkinsfile(f.path)
        return result

    def _parse_github_workflow(self, path: Path) -> dict | None:
        try:
            import yaml
            with path.open() as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return None
            info = {
                "name": data.get("name") or path.name,
                "on": list(data.get("on", {}).keys()) if isinstance(data.get("on"), dict) else str(data.get("on", "")),
                "jobs": list(data.get("jobs", {}).keys()) if isinstance(data.get("jobs"), dict) else [],
            }
            return info
        except Exception:
            return None

    def _parse_gitlab_ci(self, path: Path) -> list[dict]:
        try:
            import yaml
            with path.open() as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return []
            data.get("stages", [])
            jobs = []
            for key, val in data.items():
                if isinstance(val, dict) and "script" in val:
                    jobs.append({
                        "name": key,
                        "stage": val.get("stage", "test"),
                        "image": val.get("image", ""),
                    })
            return jobs
        except Exception:
            return []

    def _parse_circleci(self, path: Path) -> list[dict]:
        try:
            import yaml
            with path.open() as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return []
            jobs = []
            for key, val in (data.get("jobs") or {}).items():
                jobs.append({
                    "name": key,
                    "steps": len(val.get("steps", [])),
                })
            return jobs
        except Exception:
            return []

    def _parse_jenkinsfile(self, path: Path) -> list[str]:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
            stages = re.findall(r"stage\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", content)
            return stages
        except OSError:
            return []
