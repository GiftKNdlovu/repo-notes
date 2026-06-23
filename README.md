# repo-notes

Generate useful notes for any code repository from one command.

`repo-notes` scans a project and creates a readable summary of what is inside: languages, structure, dependencies, git info, architecture hints, security notes, TODOs, scripts, environment variables, type coverage, complexity, duplicate files, and API routes.

It is useful when you:

- open a new repository and want to understand it quickly
- want a compact `REPO_NOTES.md` for yourself or teammates
- want an `AGENTS.md` file for AI coding agents
- want JSON output for automation
- want a quick static-health snapshot before working on a project

It runs locally. No hosted service required.

## Installation

Requires Python 3.10 or newer.

Install the latest version from GitHub:

```bash
pip install git+https://github.com/GiftKNdlovu/repo-notes.git
```

After the package is published to PyPI, installation will be:

```bash
pip install repo-notes
```

If you are contributing locally:

```bash
git clone https://github.com/GiftKNdlovu/repo-notes.git
cd repo-notes
pip install -e .
```

## Quick start

Scan the current directory:

```bash
repo-notes .
```

This creates:

```text
REPO_NOTES.md
```

Scan another project:

```bash
repo-notes /path/to/project
```

Force a fresh scan without using the cache:

```bash
repo-notes . --no-cache
```

Write to a custom file:

```bash
repo-notes . --output docs/project-notes.md
```

## Common commands

### Generate normal project notes

```bash
repo-notes .
```

Creates `REPO_NOTES.md`.

### Generate notes quietly for scripts or CI

```bash
repo-notes . --quiet
```

Routine output is suppressed. Errors still go to stderr.

### Generate HTML output

```bash
repo-notes . --format html
```

Creates `REPO_NOTES.html`.

### Generate JSON output

```bash
repo-notes . --format json --output repo-notes.json
```

Useful for automation and downstream tools.

### Generate AI-agent context

```bash
repo-notes . --agents
```

Creates `AGENTS.md`, a compact summary designed for coding agents.

### Generate a starter README

```bash
repo-notes . --format readme
```

Creates:

```text
rnREADME.md
```

`README.md` is treated as hand-written documentation and is not overwritten by default.

To intentionally replace `README.md`, use the explicit destructive form:

```bash
repo-notes . --format readme --replace-readme --force
```

### Generate both notes and a starter README

```bash
repo-notes . --format both
```

Creates:

```text
REPO_NOTES.md
rnREADME.md
```

## Output formats

| Goal | Command | Output |
|---|---|---|
| Markdown notes | `repo-notes .` | `REPO_NOTES.md` |
| Starter README | `repo-notes . --format readme` | `rnREADME.md` |
| Notes + starter README | `repo-notes . --format both` | `REPO_NOTES.md` + `rnREADME.md` |
| HTML report | `repo-notes . --format html` | `REPO_NOTES.html` |
| JSON data | `repo-notes . --format json` | `REPO_NOTES.json` |
| Agent context | `repo-notes . --agents` | `AGENTS.md` |

## What repo-notes detects

`repo-notes` can include sections for:

- project structure
- languages and line counts
- dependency files
- git branch, remotes, contributors, and recent commits
- architecture hints, import relationships, entry points, coupling, and low-reachability candidates
- possible secrets and sensitive files
- TODO, FIXME, HACK, BUG, and similar comments
- package scripts, Makefile targets, and other build commands
- environment variables used by the project
- CI/CD configuration
- database schemas, migrations, and ORM usage
- rough type-coverage signals
- code complexity hotspots
- duplicate files
- API endpoints from common frameworks

The output is intentionally practical rather than perfect. It gives you a useful first map of a repository, not a full static-analysis platform.

## Configuration

Generate a starter config:

```bash
repo-notes . --init
```

This creates `.repo-notes.yaml`.

Example:

```yaml
exclude_patterns:
  - "*.log"
  - "build/"
  - "dist/"

include_hidden: false
min_file_size: 0

security:
  entropy_threshold: 4.5
  exclude_test_fixtures: false
  patterns: []

structure:
  max_depth: 3
  show_hidden: false

output:
  format: notes
  order:
    - structure
    - project_intelligence
    - stats
    - deps
    - git
    - arch
    - security
    - todos
    - scripts
    - env_vars
    - cicd
    - database
    - type_coverage
    - complexity
    - duplicates
    - api_endpoints
```

Use config when you want repeatable output across a team or CI job.

## CLI reference

```text
repo-notes [OPTIONS] [PATH]
```

| Option | Meaning |
|---|---|
| `PATH` | Directory to scan. Defaults to the current directory. |
| `-c, --config FILE` | Use a specific config file. |
| `-o, --output PATH` | Write output to a custom path. |
| `--max-depth INTEGER` | Control depth of the directory tree section. |
| `--include-hidden` | Include hidden files and directories. |
| `--format notes\|readme\|both\|html\|json` | Choose output format. |
| `--force` | Overwrite existing generated output files. |
| `-q, --quiet` | Suppress routine output. Useful in CI. |
| `--no-cache` | Bypass incremental cache and re-scan everything. |
| `--init` | Create a starter `.repo-notes.yaml`. |
| `--replace-readme` | Write generated README output to `README.md`. Use carefully. |
| `--agents` | Generate `AGENTS.md` for coding agents. |
| `--version` | Show installed version. |
| `--help` | Show help. |

## Notes on safety

- `README.md` is preserved by default.
- Generated starter README output goes to `rnREADME.md`.
- Existing output files are not silently overwritten unless `--force` is used where required.
- Security findings mask secret previews.
- Test-fixture/sample secrets are labelled separately from real findings when detected.

## Development

For contributors:

```bash
git clone https://github.com/GiftKNdlovu/repo-notes.git
cd repo-notes
pip install -e ".[dev]"
./scripts/check.sh
```

Run the CLI locally:

```bash
python -m repo_notes . --no-cache
```

## License

MIT
