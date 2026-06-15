"""Extractors package."""

from .structure import StructureExtractor, StructureResult
from .key_files import KeyFilesExtractor, KeyFilesResult
from .stats import StatsExtractor, StatsResult
from .dependencies import DependenciesExtractor, DependenciesResult
from .git import GitExtractor, GitResult
from .architecture import ArchitectureExtractor, ArchitectureResult
from .security import SecurityExtractor, SecurityResult
from .readme_data import ReadmeDataExtractor, ReadmeData
from .todos import TodosExtractor, TodosResult
from .scripts import ScriptsExtractor, ScriptsResult
from .env_vars import EnvVarsExtractor, EnvVarsResult

__all__ = [
    "StructureExtractor",
    "StructureResult",
    "KeyFilesExtractor",
    "KeyFilesResult",
    "StatsExtractor",
    "StatsResult",
    "DependenciesExtractor",
    "DependenciesResult",
    "GitExtractor",
    "GitResult",
    "ArchitectureExtractor",
    "ArchitectureResult",
    "SecurityExtractor",
    "SecurityResult",
    "ReadmeDataExtractor",
    "ReadmeData",
    "TodosExtractor",
    "TodosResult",
    "ScriptsExtractor",
    "ScriptsResult",
    "EnvVarsExtractor",
    "EnvVarsResult",
]