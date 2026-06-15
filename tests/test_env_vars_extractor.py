"""Tests for the environment variables extractor."""
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.extractors.env_vars import EnvVarsExtractor


def test_empty_project():
    ext = EnvVarsExtractor()
    result = ext.extract(Path("/root"), [])
    assert result.variables == {}


def test_detects_python_getenv(tmp_path: Path):
    f = tmp_path / "config.py"
    f.write_text('import os\napi_key = os.getenv("API_KEY")\n')
    files = [FileInfo(f, Path("config.py"), 40, ".py", False)]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert "API_KEY" in result.variables
    assert "config.py" in result.variables["API_KEY"]


def test_detects_os_environ_get(tmp_path: Path):
    f = tmp_path / "config.py"
    f.write_text('db = os.environ.get("DATABASE_URL")\n')
    files = [FileInfo(f, Path("config.py"), 40, ".py", False)]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert "DATABASE_URL" in result.variables


def test_detects_javascript_process_env(tmp_path: Path):
    f = tmp_path / "server.js"
    f.write_text('const port = process.env.PORT;\n')
    files = [FileInfo(f, Path("server.js"), 35, ".js", False)]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert "PORT" in result.variables


def test_detects_rust_env(tmp_path: Path):
    f = tmp_path / "main.rs"
    f.write_text('let key = env!("SECRET_KEY");\n')
    files = [FileInfo(f, Path("main.rs"), 35, ".rs", False)]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert "SECRET_KEY" in result.variables


def test_tracks_multiple_files(tmp_path: Path):
    a = tmp_path / "a.py"
    a.write_text('x = os.getenv("DB_URL")\n')
    b = tmp_path / "b.py"
    b.write_text('y = os.getenv("DB_URL")\n')
    files = [
        FileInfo(a, Path("a.py"), 25, ".py", False),
        FileInfo(b, Path("b.py"), 25, ".py", False),
    ]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert "DB_URL" in result.variables
    assert len(result.variables["DB_URL"]) == 2


def test_ignores_binary_files(tmp_path: Path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    files = [FileInfo(f, Path("data.bin"), 3, ".bin", True)]
    result = EnvVarsExtractor().extract(tmp_path, files)
    assert result.variables == {}
