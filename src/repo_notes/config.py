"""Configuration models for repo-notes."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DetectorConfig:
    enabled: list[str] = field(default_factory=lambda: ["all"])


@dataclass
class ExtractorConfig:
    structure: bool = True
    key_files: bool = True
    stats: bool = True
    dependencies: bool = True
    git: bool = True
    architecture: bool = True
    security: bool = True
    todos: bool = True
    scripts: bool = True
    env_vars: bool = True


@dataclass
class SecurityConfig:
    entropy_threshold: float = 4.5
    patterns: list[str] = field(default_factory=list)


@dataclass
class StructureConfig:
    max_depth: int = 3
    show_hidden: bool = False


@dataclass
class OutputConfig:
    format: str = "notes"
    order: list[str] = field(default_factory=lambda: [
        "structure",
        "key_files",
        "stats",
        "deps",
        "git",
        "arch",
        "security",
        "todos",
        "scripts",
        "env_vars",
    ])


@dataclass
class Config:
    exclude_patterns: list[str] = field(default_factory=list)
    include_hidden: bool = False
    min_file_size: int = 0
    detectors: DetectorConfig = field(default_factory=DetectorConfig)
    extractors: ExtractorConfig = field(default_factory=ExtractorConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    structure: StructureConfig = field(default_factory=StructureConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, root: Path | None = None, path: Path | None = None) -> "Config":
        """Load config from .repo-notes.yaml or return defaults.

        Looks for .repo-notes.yaml in the scanned root directory,
        or uses an explicit path if provided.
        """
        if path is not None:
            config_path = path
        elif root is not None:
            config_path = root / ".repo-notes.yaml"
        else:
            config_path = Path.cwd() / ".repo-notes.yaml"

        if not config_path.exists():
            return cls()
        import yaml
        with config_path.open() as f:
            data = yaml.safe_load(f) or {}
        return cls._from_dict(data)

    def merge_cli(self, **kwargs) -> "Config":
        """Create new config with CLI overrides."""
        data = self._to_dict()
        for key, value in kwargs.items():
            if value is not None:
                if key in data and isinstance(data[key], dict) and isinstance(value, dict):
                    data[key].update(value)
                else:
                    data[key] = value
        return self._from_dict(data)

    @staticmethod
    def _from_dict(data: dict) -> "Config":
        det_cfg = DetectorConfig(**data.pop("detectors", {}))
        ext_cfg = ExtractorConfig(**data.pop("extractors", {}))
        sec_cfg = SecurityConfig(**data.pop("security", {}))
        str_cfg = StructureConfig(**data.pop("structure", {}))
        out_cfg = OutputConfig(**data.pop("output", {}))
        return Config(
            detectors=det_cfg,
            extractors=ext_cfg,
            security=sec_cfg,
            structure=str_cfg,
            output=out_cfg,
            **data,
        )

    def _to_dict(self) -> dict:
        return {
            "exclude_patterns": self.exclude_patterns,
            "include_hidden": self.include_hidden,
            "min_file_size": self.min_file_size,
            "detectors": {
                "enabled": self.detectors.enabled,
            },
            "extractors": {
                "structure": self.extractors.structure,
                "key_files": self.extractors.key_files,
                "stats": self.extractors.stats,
                "dependencies": self.extractors.dependencies,
                "git": self.extractors.git,
                "architecture": self.extractors.architecture,
                "security": self.extractors.security,
                "todos": self.extractors.todos,
                "scripts": self.extractors.scripts,
                "env_vars": self.extractors.env_vars,
            },
            "security": {
                "entropy_threshold": self.security.entropy_threshold,
                "patterns": self.security.patterns,
            },
            "structure": {
                "max_depth": self.structure.max_depth,
                "show_hidden": self.structure.show_hidden,
            },
            "output": {
                "format": self.output.format,
                "order": self.output.order,
            },
        }