"""Integration tests for repo-notes."""

from pathlib import Path
import tempfile
import subprocess


def test_cli_scans_directory():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "main.py").write_text("def main(): pass\n")
        (root / "README.md").write_text("# Project\n")
        (root / "src" / "app.py").parent.mkdir()
        (root / "src" / "app.py").write_text("from flask import Flask\napp = Flask(__name__)\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Done!" in result.stdout

        output_path = root / "REPO_NOTES.md"
        assert output_path.exists()
        content = output_path.read_text()
        assert "# Repository Notes:" in content
        assert "## Project Structure" in content
        assert "## Key Files" in content
        assert "## Code Statistics" in content
        assert "main.py" in content


def test_cli_output_flag():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "hello.py").write_text("print('hello')\n")
        output = root / "custom.md"

        result = subprocess.run(
            ["repo-notes", str(root), "--output", str(output)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert output.exists()
        assert output.read_text().startswith("# Repository Notes:")


def test_cli_with_config():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "hello.py").write_text("print('hello')\n")
        (root / ".repo-notes.yaml").write_text("extractors:\n  security: false\n  architecture: false\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        output = (root / "REPO_NOTES.md").read_text()
        assert "## Security Notes" not in output


def test_cli_on_nonexistent_path():
    result = subprocess.run(
        ["repo-notes", "/nonexistent/path"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_full_pipeline():
    """End-to-end test with a realistic project structure."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Create a realistic project structure
        (root / "src" / "app" / "__init__.py").parent.mkdir(parents=True)
        (root / "src" / "app" / "main.py").write_text("""import sys
from app.service import handler

def main():
    handler()
    return 0

if __name__ == "__main__":
    sys.exit(main())
""")
        (root / "src" / "app" / "service.py").write_text("""from app.models import User

def handler():
    user = User(name="test")
    return user
""")
        (root / "src" / "app" / "models.py").write_text("""from dataclasses import dataclass

@dataclass
class User:
    name: str
""")
        (root / "tests" / "test_app.py").parent.mkdir()
        (root / "tests" / "test_app.py").write_text("""from app.main import main

def test_main():
    assert main() == 0
""")
        (root / "README.md").write_text("# My App\n\nA cool app.\n")
        (root / "pyproject.toml").write_text("""[project]
name = "my-app"
dependencies = ["click", "flask"]
""")
        (root / "requirements.txt").write_text("""click>=8.0
flask>=2.0
""")
        (root / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        result = subprocess.run(
            ["repo-notes", str(root)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        output = (root / "REPO_NOTES.md").read_text()

        # Verify all expected sections
        assert "# Repository Notes:" in output
        assert "## Project Structure" in output
        assert "## Key Files" in output
        assert "## Code Statistics" in output
        assert "## Dependencies" in output
        assert "## Architecture Overview" in output
        assert "## Security Notes" in output

        # Verify content
        assert "main.py" in output
        assert "service.py" in output
        assert "models.py" in output
        assert "README.md" in output
        assert "pyproject.toml" in output
        assert "requirements.txt" in output