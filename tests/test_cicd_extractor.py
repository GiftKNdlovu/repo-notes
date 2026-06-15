"""Tests for the CI/CD config extractor."""
from pathlib import Path

from repo_notes.extractors.cicd import CicdExtractor
from repo_notes.scanner import FileInfo


def test_empty_project():
    result = CicdExtractor().extract(Path("/root"), [])
    assert result.github_actions == []
    assert result.gitlab_ci == []
    assert result.circleci == []
    assert result.jenkins_stages == []


def test_github_actions(tmp_path: Path):
    d = tmp_path / ".github" / "workflows"
    d.mkdir(parents=True)
    f = d / "test.yml"
    f.write_text("name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n")
    files = [FileInfo(f, Path(".github/workflows/test.yml"), 100, ".yml", False)]
    result = CicdExtractor().extract(tmp_path, files)
    assert len(result.github_actions) == 1
    assert result.github_actions[0]["name"] == "CI"


def test_gitlab_ci(tmp_path: Path):
    f = tmp_path / ".gitlab-ci.yml"
    f.write_text("stages:\n  - build\n  - test\nbuild:\n  stage: build\n  script:\n    - make\n")
    files = [FileInfo(f, Path(".gitlab-ci.yml"), 60, ".yml", False)]
    result = CicdExtractor().extract(tmp_path, files)
    assert len(result.gitlab_ci) == 1
    assert result.gitlab_ci[0]["name"] == "build"


def test_circleci(tmp_path: Path):
    d = tmp_path / ".circleci"
    d.mkdir()
    f = d / "config.yml"
    f.write_text("version: 2.1\njobs:\n  build:\n    steps:\n      - run: make\n  test:\n    steps:\n      - run: pytest\n")
    files = [FileInfo(f, Path(".circleci/config.yml"), 80, ".yml", False)]
    result = CicdExtractor().extract(tmp_path, files)
    assert len(result.circleci) == 2


def test_jenkinsfile(tmp_path: Path):
    f = tmp_path / "Jenkinsfile"
    f.write_text('pipeline {\n  stages {\n    stage("Build") { steps { echo "building" } }\n    stage("Test") { steps { echo "testing" } }\n  }\n}\n')
    files = [FileInfo(f, Path("Jenkinsfile"), 100, "", False)]
    result = CicdExtractor().extract(tmp_path, files)
    assert "Build" in result.jenkins_stages
    assert "Test" in result.jenkins_stages
