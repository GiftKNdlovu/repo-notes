# Roadmap

Planned features for `repo-notes`, organized by category.

## Language Detectors

- [x] **Java** — `.java`, `.class` with Maven/Gradle entry-point detection (Spring Boot, `pom.xml`, `build.gradle`)
- [x] **C/C++** — `.c`, `.h`, `.cpp`, `.hpp`, `.cc`, `.cxx` (CMakeLists.txt, Makefile)
- [x] **Ruby** — `.rb`, `.erb` (Gemfile, Rakefile, `config/routes.rb`)
- [x] **PHP** — `.php` (composer.json, artisan, Symfony/Laravel patterns)
- [x] **Swift** — `.swift` (Package.swift)
- [x] **Kotlin** — `.kt`, `.kts` (build.gradle.kts, Android projects)
- [x] **R** — `.r`, `.rmd`
- [x] **Shell/Scripting** — `.sh`, `.bash`, `.zsh`, `.ps1`
- [x] **SQL** — `.sql` with migration folder detection
- [x] **Docker** — `Dockerfile`, `docker-compose` as a pseudo-language

## Output Improvements

- [ ] **README generation** — auto-generate a README alongside or instead of REPO_NOTES.md
- [x] **Summary badges** at the top — total files, lines, languages, security issues
- [x] **Syntax-highlighted code blocks** — correct language identifiers in markdown fences
- [x] **Collapsible sections** — `<details>` tags for large output
- [ ] **HTML output** option for a pretty web view
- [x] **Section ordering** — user-configurable section order via `.repo-notes.yaml`

## Performance

- [ ] **Parallel file scanning** — `concurrent.futures` for git and security extractors
- [ ] **File content caching** — share file reads across extractors instead of re-reading
- [ ] **Incremental updates** — only re-scan changed files using content hashes
- [ ] **Streaming output** — write progressively for very large repos

## New Extractors

- [ ] **TODO/FIXME/HACK extraction** — surface developer comments across all languages
- [ ] **API endpoint detection** — routes from Flask, FastAPI, Django, Express, Rails
- [ ] **CI/CD config parsing** — GitHub Actions, GitLab CI, CircleCI, Jenkinsfile
- [ ] **Database schema** — SQL migrations, ORM models (SQLAlchemy, Prisma, ActiveRecord)
- [ ] **Environment variables consumed** — scan for `os.getenv`, `process.env`, `env!()`
- [ ] **Scripts section** — `package.json` scripts, Makefile targets, justfile
- [ ] **Type coverage** — rough estimate of typed vs untyped code (type hints, TypeScript types)
- [ ] **Code complexity** — cyclomatic complexity per file (long functions, nesting depth)
- [ ] **Duplicate detection** — near-duplicate file detection via tokens or line hashes

## Architecture Analysis

- [ ] **Import graph visualization** — Mermaid.js flow diagram
- [ ] **Component dependency matrix** — which files/modules import which
- [ ] **Circular dependency detection**
- [ ] **Module coupling score** — per file/module
- [ ] **Dead code candidates** — leaf files no other file imports
- [ ] **Microservice boundary detection** — based on import/reference patterns

## Package & Distribution

- [ ] **PyPI publishing** — `pyproject.toml` metadata for twine/flit
- [ ] **CI/CD** — GitHub Actions for lint + test on PR, publish on tag
- [ ] **Pre-commit hook** — `.pre-commit-hooks.yaml` for `repo-notes` on commit
- [ ] **Docker image** — Dockerfile for running without local Python

## Developer Experience

- [ ] **`--watch` / `-w`** — re-scan on file changes (watchdog)
- [ ] **`--diff`** — compare current notes against last commit's version
- [ ] **`--init`** — generate a `.repo-notes.yaml` template in the project
- [ ] **`--json` output** — machine-readable for editor plugins
- [ ] **Auto-detect git root** — scan repo root even from a subdirectory
- [ ] **`--quiet` / `-q`** — suppress progress bars (CI-friendly)
- [ ] **Tab-completion** — shell completion scripts (click built-in)

## Config Refinements

- [ ] **Per-extractor options** — fine-grained toggle in config (e.g. `security.patterns`, `structure.max_depth`)
- [ ] **Custom secret patterns** — user-defined regex patterns for secret scanning
- [ ] **Custom layer patterns** — user-defined path patterns for architecture layer detection
- [ ] **Per-path extractor exclusion** — skip specific extractors on vendored/generated code
- [ ] **Config profiles** — presets like `release`, `ci`, `quick`
- [ ] **Thresholds** — min file size, max lines for stats inclusion, etc.

## Testing & Quality

- [ ] **Coverage target** — minimum coverage threshold in CI
- [ ] **Property-based tests** — via `hypothesis` for extractors
- [ ] **Benchmark suite** — measure scan time on known repos
- [ ] **Snapshot tests** — golden file tests for markdown output

---

**Total: ~50 features across 9 categories.**
