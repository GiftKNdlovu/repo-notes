# repo-notes

A small Python CLI tool that scans a code repository and generates a comprehensive `REPO_NOTES.md` file with useful project notes. Helps developers quickly understand a repo without manually reading every file.

## Quick Start

```bash
pip install repo-notes

# Scan the current directory
repo-notes

# Scan a specific project
repo-notes /path/to/project

# Open the generated notes
cat REPO_NOTES.md
```

## Features

- **Project Structure** — hierarchical directory tree
- **Key Files** — detects README, LICENSE, CI configs, entry points, and more
- **Code Statistics** — total LOC, file counts per language, largest files
- **Dependencies** — parses `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`
- **Git Information** — recent commits, branches, top contributors
- **Architecture Overview** — layer detection (routes, services, models), entry points, import graph
- **Security Notes** — detects potential secrets (AWS keys, API tokens, DB URLs) and `.env` files
- **Multi-language** — Python, JavaScript/TypeScript, Go, Rust (extensible registry)

## Installation

### From source

```bash
git clone https://github.com/GiftKNdlovu/repo-note.git
cd repo-note
pip install .
```

### Development install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
Usage: repo-notes [OPTIONS] [PATH]

  Scan REPO_PATH and generate REPO_NOTES.md with project notes.
  By default, scans the current directory.

Options:
  -c, --config FILE    Path to config file
  -o, --output PATH    Output file path (default: REPO_NOTES.md)
  --max-depth INTEGER  Max depth for directory tree (default: 3)
  --include-hidden     Include hidden files and directories
  --help               Show this message and exit.
```

## Configuration

Place a `.repo-notes.yaml` in your project root to customize behaviour:

```yaml
# Additional exclusion patterns (beyond .gitignore)
exclude_patterns:
  - "*.log"
  - "dist/"

# Include hidden files (dotfiles)
include_hidden: false

# Language detectors to enable
detectors:
  enabled:
    - all  # or list specific: ["python", "javascript"]

# Content extractors to run
extractors:
  structure: true
  key_files: true
  stats: true
  dependencies: true
  git: true
  architecture: true
  security: true

# Structure tree settings
structure:
  max_depth: 3

# Security scanning
security:
  entropy_threshold: 4.5  # Shannon entropy (lower = more sensitive)
```

### Example Config

```bash
# Use a custom config file
repo-notes --config /path/to/.repo-notes.yaml

# CLI flags override config values
repo-notes --max-depth 5 --include-hidden
```

## Architecture

```
src/repo_notes/
├── __init__.py          # Package metadata
├── __main__.py          # Entry point
├── cli.py               # Click CLI with progress bar
├── scanner.py           # File discovery + .gitignore support
├── config.py            # YAML config loading
├── generator.py         # Markdown composition
├── detectors/           # Language detection
│   ├── base.py          # Abstract interface
│   ├── registry.py      # Auto-discovery registry
│   ├── python.py        # .py, .pyi, .pyx
│   ├── javascript.py    # .js, .jsx, .ts, .tsx
│   ├── go.py            # .go
│   └── rust.py          # .rs
└── extractors/          # Content extraction
    ├── structure.py     # Directory tree
    ├── key_files.py     # README, configs, entry points
    ├── stats.py         # LOC, file counts
    ├── dependencies.py  # Package managers
    ├── git.py           # Commits, branches
    ├── architecture.py  # Layer detection, imports
    └── security.py      # Secret patterns, entropy
```

## Adding a New Language Detector

```python
from repo_notes.detectors.base import ExtensionDetector, LanguageInfo

MY_LANG_INFO = LanguageInfo(
    name="my_lang",
    category="backend",
    extensions=frozenset({".foo", ".bar"}),
)

class MyLangDetector(ExtensionDetector):
    def __init__(self):
        super().__init__(MY_LANG_INFO)
```

Then register it in `src/repo_notes/detectors/registry.py`:

```python
from . import my_lang
registry.register(my_lang.MyLangDetector())
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/

# Run on itself
repo-notes .
```

## Requirements

- Python >= 3.10
- Dependencies: `click`, `pyyaml`, `pathspec`, `rich`

## License

MIT
