# repo-notes

Scan any code repository and generate comprehensive project notes, including code statistics, git history, security scans, architecture analysis, and more.

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.10-yellow)
![Tests](https://img.shields.io/badge/tests-152%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Quick Start

```bash
pip install repo-notes
```

Scan a project and generate notes:

```bash
repo-notes /path/to/project
```

This creates `REPO_NOTES.md` with all available information about the project.

## Output Formats

| Format | Command | Output File |
|--------|---------|-------------|
| Notes (default) | `repo-notes .` | `REPO_NOTES.md` |
| README | `repo-notes . --format readme` | `rnREADME.md` |
| README (overwrite) | `repo-notes . --format readme --replace-readme --force` | `README.md` |
| Both | `repo-notes . --format both` | `REPO_NOTES.md` + `rnREADME.md` |
| HTML | `repo-notes . --format html` | `REPO_NOTES.html` |
| JSON | `repo-notes . --format json` | `REPO_NOTES.json` |

## CLI Reference

| Flag | Description |
|------|-------------|
| `PATH` | Directory to scan (default: current directory) |
| `-c, --config PATH` | Path to `.repo-notes.yaml` config file |
| `-o, --output PATH` | Output file path (default: `REPO_NOTES.md`) |
| `--format {notes,readme,both,html,json}` | Output format |
| `--replace-readme` | Write to `README.md` instead of `rnREADME.md` |
| `--force` | Overwrite existing output files |
| `--max-depth N` | Maximum depth for directory tree (default: 3) |
| `--include-hidden` | Include hidden files and directories |
| `-q, --quiet` | Suppress progress output (for CI) |
| `--no-cache` | Bypass incremental cache, force full re-scan |
| `--init` | Generate a `.repo-notes.yaml` template |
| `--help` | Show help message |

## Output Sections

Once generated, the notes contain up to 10 sections:

### 1. Project Structure
Directory tree of the project with file/directory counts. Respects `.gitignore` and excludes common build artifacts by default. Depth configurable via `--max-depth`.

### 2. Key Files
Detects important project files automatically: README, LICENSE, CHANGELOG, CONTRIBUTING, CI configs (GitHub Actions, GitLab CI, CircleCI, etc.), Docker files, config files, and entry points.

### 3. Code Statistics
Total files, lines of code, size breakdown by language. Supports 10+ languages with automatic detection. Shows largest files and language distribution tables.

### 4. Dependencies
Extracts dependencies from:
- **Python**: `requirements.txt`, `pyproject.toml`, `setup.py`, `setup.cfg`
- **JavaScript/TypeScript**: `package.json`, lockfiles
- **Go**: `go.mod`, `go.sum`
- **Rust**: `Cargo.toml`, `Cargo.lock`

### 5. Git Information
Shows current branch, remote URL, recent commits, all branches, and top contributors. Only appears when run inside a git repository.

### 6. Architecture Overview
Detects application layers (entry points, models, controllers, views, routes, middleware, services, config, tests, migrations) by analyzing file paths and naming conventions.

### 7. Security Notes
Scans for potential secrets and sensitive files:
- **High severity**: Pattern-matched secrets (AWS keys, GitHub tokens, database URLs, private keys, JWT secrets)
- **Mild severity**: High-entropy strings that may contain secrets
- **Custom patterns**: User-defined regex patterns via `security.patterns` in config
- Environment files (`.env*`) are flagged with warnings

### 8. TODO / FIXME / HACK
Scans all non-binary files for developer comments tagged with `TODO`, `FIXME`, `HACK`, `XXX`, `BUG`, `WORKAROUND`, or `HACKME`. Shows file, line number, and the comment message.

### 9. Build Scripts
Extracts executable targets from:
- **package.json**: npm scripts
- **Makefile**: make targets
- **justfile**: just recipes
- **pyproject.toml**: console scripts (setuptools, hatch, poetry, flit)

### 10. Environment Variables
Scans all files for environment variable access patterns:
- **Python**: `os.getenv("VAR")`, `os.environ.get("VAR")`
- **JavaScript/TypeScript**: `process.env.VAR`
- **Rust**: `env!("VAR")`
- **Shell**: `$VAR`, `${VAR}`
- **Generic**: `getenv("VAR")` calls

Shows each unique variable name and which files reference it.

## Performance Features

- **Parallel scanning**: Directory walk uses `os.scandir` (zero-stat traversal) with per-file processing distributed across a thread pool
- **Parallel extractors**: All enabled extractors run concurrently via `ThreadPoolExecutor`
- **File content caching**: Shared `@lru_cache` across extractors eliminates redundant file reads
- **Streaming output**: Markdown and HTML generators write progressively without building full output in memory
- **Incremental caching**: `.repo-notes-cache.json` persists file metadata (mtime, size, content hash). Subsequent runs skip the full scan if nothing changed
- **`--no-cache`**: Bypass incremental cache for forced re-scan

## Configuration

Create a `.repo-notes.yaml` file in the project root (or generate one with `repo-notes . --init`):

```yaml
# Directories or files to exclude (gitignore-style patterns)
exclude_patterns:
  - "*.log"
  - "build/"

# Include hidden files and directories
include_hidden: false

# Minimum file size in bytes (files smaller than this are skipped)
min_file_size: 0

# Which extractors to run
extractors:
  structure: true
  key_files: true
  stats: true
  dependencies: true
  git: true
  architecture: true
  security: true
  todos: true
  scripts: true
  env_vars: true

# Security scanner options
security:
  entropy_threshold: 4.5
  patterns: []  # custom regex patterns for secret detection

# Directory tree options
structure:
  max_depth: 3
  show_hidden: false

# Output options
output:
  format: notes  # notes, readme, both, html, or json
  order:
    - structure
    - key_files
    - stats
    - deps
    - git
    - arch
    - security
    - todos
    - scripts
    - env_vars
```

The `output.order` list lets you reorder sections arbitrarily. Any section without data is automatically omitted.

## Language Detection

repo-notes detects the following languages for statistics and syntax highlighting:

Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, Ruby, PHP, Swift, Kotlin, R, Shell, SQL, Docker

Detection is based on file extension and project conventions (e.g., `Dockerfile`, `Gemfile`, `Rakefile`).

## Development

```bash
# Install from source
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/repo_notes

# Lint
ruff check src/ tests/
```

## Project Structure

```
src/repo_notes/
├── __init__.py          # Version
├── __main__.py          # Entry point
├── cli.py               # CLI with click
├── config.py            # YAML config model
├── cache.py             # Incremental scan cache
├── scanner.py           # File system scanner (parallel)
├── file_cache.py        # Shared content cache (lru_cache)
├── generator.py         # Markdown output generator
├── html_generator.py    # HTML output generator
├── html_templates.py    # HTML/CSS/JS templates
├── readme_generator.py  # README.md generator
├── detectors/           # Language detectors
│   ├── base.py
│   ├── registry.py
│   ├── python.py
│   ├── javascript.py
│   ├── go.py
│   ├── rust.py
│   └── ... (10 languages)
└── extractors/          # Data extractors
    ├── structure.py
    ├── key_files.py
    ├── stats.py
    ├── dependencies.py
    ├── git.py
    ├── architecture.py
    ├── security.py
    ├── todos.py
    ├── scripts.py
    ├── env_vars.py
    └── readme_data.py
tests/
├── test_scanner.py
├── test_extractors.py
├── test_generator.py
├── test_html_generator.py
├── test_readme_generator.py
├── test_integration.py
├── test_cache.py
├── test_detectors.py
├── test_todos_extractor.py
├── test_scripts_extractor.py
└── test_env_vars_extractor.py
benchmarks/
└── benchmark.py
```

## License

MIT
