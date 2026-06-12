"""Git information extractor."""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess


@dataclass(slots=True)
class GitResult:
    is_repo: bool = False
    recent_commits: list[dict[str, str]] = field(default_factory=list)
    branches: list[str] = field(default_factory=list)
    contributors: list[dict[str, int]] = field(default_factory=list)
    current_branch: str = ""
    remote_url: str = ""


class GitExtractor:
    def extract(self, root: Path, files: list) -> GitResult:
        if not (root / ".git").exists():
            return GitResult(is_repo=False)

        result = GitResult(is_repo=True)
        result.current_branch = self._run_git(root, ["branch", "--show-current"]).strip()
        result.remote_url = self._run_git(root, ["config", "--get", "remote.origin.url"]).strip()

        # Recent commits (last 10)
        log_output = self._run_git(root, [
            "log", "-10", "--pretty=format:%H|%an|%ad|%s", "--date=short"
        ])
        for line in log_output.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 3)
            if len(parts) == 4:
                result.recent_commits.append({
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                })

        # Branches
        branches_output = self._run_git(root, ["branch", "-a", "--format=%(refname:short)"])
        result.branches = [b.strip() for b in branches_output.strip().split("\n") if b.strip()]

        # Top contributors
        contributors_output = self._run_git(root, [
            "shortlog", "-sn", "--all"
        ])
        for line in contributors_output.strip().split("\n"):
            if not line:
                continue
            parts = line.strip().split("\t", 1)
            if len(parts) == 2:
                result.contributors.append({
                    "name": parts[1],
                    "commits": int(parts[0]),
                })

        return result

    def _run_git(self, root: Path, args: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout
        except Exception:
            return ""