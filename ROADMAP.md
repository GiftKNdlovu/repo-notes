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

- [x] **README generation** — auto-generate a README alongside or instead of REPO_NOTES.md
- [x] **Summary badges** at the top — total files, lines, languages, security issues
- [x] **Syntax-highlighted code blocks** — correct language identifiers in markdown fences
- [x] **Collapsible sections** — `<details>` tags for large output
- [x] **HTML output** option for a pretty web view
- [x] **Section ordering** — user-configurable section order via `.repo-notes.yaml`

## Performance

- [x] **Parallel file scanning** — `concurrent.futures` for all extractors
- [x] **File content caching** — share file reads across extractors via `@lru_cache`
- [x] **Incremental updates** — `.repo-notes-cache.json` tracks file mtime/size/hash, skips scan if unchanged
- [x] **Streaming output** — write progressively to file via `write_to()` methods

## New Extractors

- [x] **TODO/FIXME/HACK extraction** — surface developer comments across all languages
- [ ] **API endpoint detection** — routes from Flask, FastAPI, Django, Express, Rails
- [x] **CI/CD config parsing** — GitHub Actions, GitLab CI, CircleCI, Jenkinsfile
- [x] **Database schema** — SQL migrations, ORM models (SQLAlchemy, Prisma, ActiveRecord)
- [x] **Environment variables consumed** — scan for `os.getenv`, `process.env`, `env!()`
- [x] **Scripts section** — `package.json` scripts, Makefile targets, justfile
- [x] **Type coverage** — rough estimate of typed vs untyped code (type hints, TypeScript types)
- [x] **Code complexity** — cyclomatic complexity per file (long functions, nesting depth)
- [x] **Duplicate detection** — near-duplicate file detection via tokens or line hashes

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
- [x] **`--init`** — generate a `.repo-notes.yaml` template in the project
- [x] **`--json` output** — machine-readable via `--format json`
- [x] **Auto-detect git root** — scan repo root even from a subdirectory
- [x] **`--quiet` / `-q`** — suppress progress bars (CI-friendly)
- [ ] **Tab-completion** — shell completion scripts (click built-in)

## Config Refinements

- [ ] **Per-extractor options** — fine-grained toggle in config (e.g. `security.patterns`, `structure.max_depth`)
- [x] **Custom secret patterns** — user-defined regex patterns in config `security.patterns`
- [ ] **Custom layer patterns** — user-defined path patterns for architecture layer detection
- [ ] **Per-path extractor exclusion** — skip specific extractors on vendored/generated code
- [ ] **Config profiles** — presets like `release`, `ci`, `quick`
- [x] **Thresholds** — `min_file_size` config option

## Testing & Quality

- [ ] **Coverage target** — minimum coverage threshold in CI
- [ ] **Property-based tests** — via `hypothesis` for extractors
- [x] **Benchmark suite** — `benchmarks/benchmark.py` measures scan time on synthetic repos
- [ ] **Snapshot tests** — golden file tests for markdown output

---

**Total: ~50 features across 9 categories.**
