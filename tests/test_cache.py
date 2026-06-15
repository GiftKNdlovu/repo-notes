"""Tests for the incremental cache."""
import json
from pathlib import Path

from repo_notes.cache import CacheManager, FileState, _config_hash
from repo_notes.config import Config


def test_cache_save_and_load(tmp_path: Path):
    cfg = Config()
    cache = CacheManager(tmp_path, cfg)
    states = {
        "main.py": FileState(mtime=1000, size=50, hash="abc"),
        "util.py": FileState(mtime=1001, size=30, hash="def"),
    }
    cache.save(states)
    assert cache.cache_path.exists()
    data = json.loads(cache.cache_path.read_text())
    assert data["version"] == 1
    assert "config_hash" in data
    assert data["files"]["main.py"]["size"] == 50


def test_cache_load_missing(tmp_path: Path):
    cfg = Config()
    cache = CacheManager(tmp_path, cfg)
    assert cache.load() == {}
    assert cache.is_valid() is False


def test_cache_is_valid_after_save(tmp_path: Path):
    cfg = Config()
    cache = CacheManager(tmp_path, cfg)
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})
    # Config unchanged → should be valid
    assert cache.is_valid() is True


def test_cache_invalid_on_config_change(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})

    # Different config (changed include_hidden)
    cfg2 = Config()
    cfg2.include_hidden = True
    cache2 = CacheManager(tmp_path, cfg2)
    assert cache2.is_valid() is False


def test_cache_has_changes_new_file(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})

    current = {
        "main.py": FileState(mtime=1000, size=50, hash="abc"),
        "new.py": FileState(mtime=1002, size=20, hash="xyz"),
    }
    assert cache.has_changes(current) is True


def test_cache_has_changes_removed_file(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({
        "main.py": FileState(mtime=1000, size=50, hash="abc"),
        "util.py": FileState(mtime=1001, size=30, hash="def"),
    })

    current = {
        "main.py": FileState(mtime=1000, size=50, hash="abc"),
    }
    assert cache.has_changes(current) is True


def test_cache_has_changes_no_change(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})

    current = {
        "main.py": FileState(mtime=1000, size=50, hash="abc"),
    }
    assert cache.has_changes(current) is False


def test_cache_has_changes_mtime_change(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})

    current = {
        "main.py": FileState(mtime=2000, size=50, hash="abc"),
    }
    assert cache.has_changes(current) is True


def test_cache_has_changes_size_change(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"main.py": FileState(mtime=1000, size=50, hash="abc")})

    current = {
        "main.py": FileState(mtime=1000, size=99, hash="abc"),
    }
    assert cache.has_changes(current) is True


def test_cache_clear(tmp_path: Path):
    cache = CacheManager(tmp_path, Config())
    cache.save({"f.py": FileState(mtime=1, size=1, hash="a")})
    assert cache.cache_path.exists()
    cache.clear()
    assert not cache.cache_path.exists()
    assert cache.load() == {}


def test_config_hash_changes(tmp_path: Path):
    """Different configs produce different hashes."""
    c1 = Config()
    c2 = Config()
    c2.include_hidden = True
    assert _config_hash(c1) != _config_hash(c2)


def test_cache_detects_real_file_changes(tmp_path: Path):
    """Integration test: mock files and verify cache detects changes."""
    (tmp_path / "a.py").write_text("x = 1\n")
    cfg = Config()
    cache = CacheManager(tmp_path, cfg)

    current = cache.compute_current_states()
    assert "a.py" in current

    # First save
    cache.save(current)
    assert cache.is_valid()
    assert not cache.has_changes(cache.compute_current_states())

    # Modify file
    (tmp_path / "a.py").write_text("x = 2\n")
    assert cache.has_changes(cache.compute_current_states())


def test_cache_save_from_file_infos(tmp_path: Path):
    """save_from_file_infos correctly persists scanned files."""
    (tmp_path / "a.py").write_text("x = 1\n")
    cfg = Config()
    cache = CacheManager(tmp_path, cfg)

    # Simulate what cli.py does
    from repo_notes.scanner import scan_directory
    files = list(scan_directory(tmp_path))
    cache.save_from_file_infos(files)

    assert cache.cache_path.exists()
    data = json.loads(cache.cache_path.read_text())
    assert "a.py" in data["files"]


def test_cache_compute_current_states(tmp_path: Path):
    """compute_current_states returns states for all non-ignored files."""
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "b.ts").write_text("const x = 1;\n")
    (tmp_path / "ignored.pyc").write_text("ignored")

    cfg = Config()
    cache = CacheManager(tmp_path, cfg)
    states = cache.compute_current_states()

    assert "a.py" in states
    assert "b.ts" in states
    assert "ignored.pyc" not in states  # .pyc files excluded by default
