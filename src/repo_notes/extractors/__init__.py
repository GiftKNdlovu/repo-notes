"""Extractors package."""

from .structure import StructureExtractor, StructureResult
from .key_files import KeyFilesExtractor, KeyFilesResult
from .stats import StatsExtractor, StatsResult
from .dependencies import DependenciesExtractor, DependenciesResult
from .git import GitExtractor, GitResult
from .architecture import ArchitectureExtractor, ArchitectureResult
from .security import SecurityExtractor, SecurityResult
from .readme_data import ReadmeDataExtractor, ReadmeData

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
]