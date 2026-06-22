"""Docker language detector (matched by filename, not extension)."""

from pathlib import Path

from .base import LanguageDetector, LanguageInfo

DOCKER_INFO = LanguageInfo(
    name="docker",
    category="infra",
    extensions=frozenset(),
)

_DOCKER_FILENAMES = frozenset({
    "dockerfile", "docker-compose.yml", "docker-compose.yaml",
    "docker-compose.override.yml", "docker-compose.override.yaml",
})


class DockerDetector(LanguageDetector):
    """Detect Dockerfiles and docker-compose files by exact filename."""

    @property
    def language_info(self) -> LanguageInfo:
        return DOCKER_INFO

    def classify(self, path: Path, content_preview: str | None = None) -> LanguageInfo | None:
        if path.name.lower() in _DOCKER_FILENAMES or path.suffix.lower() == ".dockerfile":
            return DOCKER_INFO
        return None
