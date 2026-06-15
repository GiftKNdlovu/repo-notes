"""Extractor for database schema and ORM model detection."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text


MIGRATION_DIR_PATTERNS = ["migrations", "migration", "db/migrate", "alembic", "prisma/"]
ORM_DETECTORS = [
    (r"class\s+\w+\s*\(.*\bBase\b", "SQLAlchemy"),
    (r"class\s+\w+\s*\(.*\bmodels?\.Model\b", "Django"),
    (r"model\s+\w+\s*\{", "Prisma"),
    (r"create_table\s+:\w+", "ActiveRecord"),
]


@dataclass(slots=True)
class DatabaseResult:
    migration_files: list[Path] = field(default_factory=list)
    model_files: list[Path] = field(default_factory=list)
    model_count: int = 0
    schema_files: list[Path] = field(default_factory=list)
    orm_types: list[str] = field(default_factory=list)


class DatabaseExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> DatabaseResult:
        migration_files: list[Path] = []
        model_files: list[Path] = []
        schema_files: list[Path] = []
        orm_types: set[str] = set()
        model_count = 0

        for f in files:
            if f.is_binary:
                continue
            rel = f.relative_path
            rel_str = rel.as_posix()

            # Detect migration files by path
            if any(p in rel_str for p in MIGRATION_DIR_PATTERNS):
                migration_files.append(rel)
                continue

            # Detect schema files
            if rel.name in ("schema.prisma", "schema.rb", "models.py"):
                schema_files.append(rel)

            # Detect ORM models in content
            content = read_text(f.path)
            if not content:
                continue
            for pattern, orm_name in ORM_DETECTORS:
                if re.search(pattern, content):
                    orm_types.add(orm_name)
                    model_files.append(rel)
                    model_count += len(re.findall(r"class\s+\w+", content))
                    break

        return DatabaseResult(
            migration_files=sorted(set(migration_files)),
            model_files=sorted(set(model_files)),
            model_count=model_count,
            schema_files=sorted(set(schema_files)),
            orm_types=sorted(orm_types),
        )
