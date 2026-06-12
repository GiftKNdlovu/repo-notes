"""Tests for extractor modules."""

from pathlib import Path
from repo_notes.scanner import FileInfo, scan_directory
from repo_notes.extractors.structure import StructureExtractor
from repo_notes.extractors.key_files import KeyFilesExtractor
from repo_notes.extractors.stats import StatsExtractor
from repo_notes.extractors.security import SecurityExtractor
from repo_notes.extractors.git import GitExtractor


SAMPLE_FILES = [
    FileInfo(Path("/root/main.py"), Path("main.py"), 100, ".py", False),
    FileInfo(Path("/root/src/app.py"), Path("src/app.py"), 200, ".py", False),
    FileInfo(Path("/root/src/models/user.py"), Path("src/models/user.py"), 150, ".py", False),
    FileInfo(Path("/root/README.md"), Path("README.md"), 50, ".md", False),
    FileInfo(Path("/root/requirements.txt"), Path("requirements.txt"), 30, ".txt", False),
    FileInfo(Path("/root/.env"), Path(".env"), 20, "", False),
    FileInfo(Path("/root/data.bin"), Path("data.bin"), 100, ".bin", True),
    FileInfo(Path("/root/LICENSE"), Path("LICENSE"), 1000, "", False),
    FileInfo(Path("/root/Makefile"), Path("Makefile"), 80, "", False),
]


class TestStructureExtractor:
    def test_basic_tree(self):
        extractor = StructureExtractor(max_depth=3)
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert result.file_count == 9
        assert "main.py" in result.tree
        assert "src/" in result.tree
        assert "models/" in result.tree

    def test_max_depth_filters(self):
        extractor = StructureExtractor(max_depth=1)
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        # Should only show root-level files and 1 level of dirs
        assert "main.py" in result.tree
        assert "src/" in result.tree
        assert "models/" not in result.tree


class TestKeyFilesExtractor:
    def test_detects_readme(self):
        extractor = KeyFilesExtractor()
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert "readme" in result.categories
        assert Path("README.md") in result.categories["readme"]

    def test_detects_entry_point(self):
        extractor = KeyFilesExtractor()
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert "entrypoint" in result.categories
        assert Path("main.py") in result.categories["entrypoint"]

    def test_detects_license(self):
        extractor = KeyFilesExtractor()
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert "license" in result.categories
        assert Path("LICENSE") in result.categories["license"]


class TestStatsExtractor:
    def test_basic_counts(self):
        extractor = StatsExtractor()
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert result.total_files == 9

    def test_largest_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "big.py").write_text("\n".join(f"x{i} = {i}" for i in range(100)))
            (root / "small.py").write_text("x = 1")
            files = list(scan_directory(root))
            extractor = StatsExtractor(top_n=3)
            result = extractor.extract(root, files)
            assert result.largest_files[0][0] == Path("big.py")
            assert result.largest_files[0][1] >= 100


class TestSecurityExtractor:
    def test_detects_env_file(self):
        extractor = SecurityExtractor()
        result = extractor.extract(Path("/root"), SAMPLE_FILES)
        assert Path(".env") in result.env_files

    def test_detects_aws_key(self):
        extractor = SecurityExtractor()
        files = [
            FileInfo(Path("/root/config.py"), Path("config.py"), 50, ".py", False),
        ]
        files[0] = FileInfo(
            path=Path("/root/config.py"),
            relative_path=Path("config.py"),
            size=50,
            extension=".py",
            is_binary=False,
        )
        # Write the content directly for testing
        content = 'aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"'
        with Path("/tmp/test_config.py").open("w") as f:
            f.write(content)
        test_file = FileInfo(
            path=Path("/tmp/test_config.py"),
            relative_path=Path("config.py"),
            size=len(content),
            extension=".py",
            is_binary=False,
        )
        result = extractor.extract(Path("/tmp"), [test_file])
        assert any(f["type"] == "AWS Access Key" for f in result.findings)
        Path("/tmp/test_config.py").unlink(missing_ok=True)

    def test_high_entropy_detection(self):
        extractor = SecurityExtractor(entropy_threshold=3.0)
        content = "aB3dEfGhIjKlMnOpQrStUvWxYz0123456789abcdef"  # high entropy
        with Path("/tmp/test_entropy.py").open("w") as f:
            f.write(f"secret = '{content}'")
        test_file = FileInfo(
            path=Path("/tmp/test_entropy.py"),
            relative_path=Path("config.py"),
            size=len(content) + 10,
            extension=".py",
            is_binary=False,
        )
        result = extractor.extract(Path("/tmp"), [test_file])
        assert len(result.high_entropy_strings) > 0
        Path("/tmp/test_entropy.py").unlink(missing_ok=True)


class TestGitExtractor:
    def test_no_git_repo(self):
        extractor = GitExtractor()
        result = extractor.extract(Path("/tmp"), [])
        assert not result.is_repo