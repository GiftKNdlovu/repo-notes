"""Tests for the database schema extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.database import DatabaseExtractor


def test_empty_project():
    result = DatabaseExtractor().extract(Path("/root"), [])
    assert result.migration_files == []
    assert result.model_files == []


def test_detects_migration_dir(tmp_path: Path):
    d = tmp_path / "migrations"
    d.mkdir()
    f = d / "001_init.sql"
    f.write_text("CREATE TABLE users;")
    files = [FileInfo(f, Path("migrations/001_init.sql"), 25, ".sql", False)]
    result = DatabaseExtractor().extract(tmp_path, files)
    assert len(result.migration_files) == 1


def test_detects_sqlalchemy_models(tmp_path: Path):
    f = tmp_path / "models.py"
    f.write_text("from sqlalchemy import Column\nfrom sqlalchemy.ext.declarative import declarative_base\nBase = declarative_base()\nclass User(Base):\n    __tablename__ = 'users'\n    id = Column(Integer, primary_key=True)\n")
    files = [FileInfo(f, Path("models.py"), 160, ".py", False)]
    result = DatabaseExtractor().extract(tmp_path, files)
    assert "SQLAlchemy" in result.orm_types
    assert Path("models.py") in result.model_files


def test_detects_prisma(tmp_path: Path):
    f = tmp_path / "schema.prisma"
    f.write_text("model User {\n  id    Int     @id\n  email String\n}\n")
    files = [FileInfo(f, Path("schema.prisma"), 45, ".prisma", False)]
    result = DatabaseExtractor().extract(tmp_path, files)
    assert Path("schema.prisma") in result.schema_files


def test_detects_alembic_dir(tmp_path: Path):
    d = tmp_path / "alembic" / "versions"
    d.mkdir(parents=True)
    f = d / "0001_create_users.py"
    f.write_text("def upgrade(): pass\n")
    files = [FileInfo(f, Path("alembic/versions/0001_create_users.py"), 30, ".py", False)]
    result = DatabaseExtractor().extract(tmp_path, files)
    assert len(result.migration_files) == 1
