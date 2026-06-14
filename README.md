# repo-notes

Scan a code repository and generate useful project notes

![Version](https://img.shields.io/badge/version-0.1.0-blue) ![Python](https://img.shields.io/badge/python-%3E%3D3.10-yellow) ![Tests](https://img.shields.io/badge/tests-passing-brightgreen)

## Quick Start

```bash
pip install repo-notes
```

## Features

- **4 runtime dependencies** — click, pyyaml, pathspec, rich
- **Test suite** — ready for development

## Usage

```
repo-notes [OPTIONS] [PATH]
```

## Project Structure

```
repo-notes-opencode/
README.md
REPO_NOTES.md
ROADMAP.md
pyproject.toml
src/
  repo_notes/
    __init__.py
    __main__.py
    cli.py
    config.py
    detectors/
      __init__.py
      base.py
      go.py
      javascript.py
      python.py
      registry.py
      rust.py
    extractors/
      __init__.py
      architecture.py
      dependencies.py
      git.py
      key_files.py
      readme_data.py
      security.py
      stats.py
      structure.py
    generator.py
    readme_generator.py
    scanner.py
test_results.txt
tests/
  __init__.py
  test_detectors.py
  test_extractors.py
  test_generator.py
  test_integration.py
  test_readme_generator.py
  test_scanner.py
```

## Code Statistics

- **Total files**: 35
- **Total lines**: 3,430
- **Languages**: python: 30 files, 2930 lines, unknown: 5 files, 500 lines

## Development

```bash
pip install -e ".[dev]"
```

### Commands

```bash
# Run tests
pytest

# Run linter
ruff check src/ tests/
```

## License

MIT
