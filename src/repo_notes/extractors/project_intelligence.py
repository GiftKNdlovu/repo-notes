"""Project Intelligence — deep detection of tools, frameworks, configs."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text


@dataclass(slots=True)
class DetectedTool:
    name: str
    version: str | None = None
    config_file: str | None = None
    category: str = ""


@dataclass(slots=True)
class ProjectIntelligenceResult:
    tools: dict[str, list[DetectedTool]] = field(default_factory=dict)
    categories: dict[str, list[Path]] = field(default_factory=dict)
    total_tools: int = 0
    total_categories: int = 0

    def __post_init__(self):
        self.total_tools = sum(len(v) for v in self.tools.values())
        self.total_categories = len(self.tools)


_TOOL_DEFS: list[dict] = [
    # === Testing ===
    {"name": "pytest", "category": "Testing", "filenames": ["pytest.ini", "conftest.py"], "content_files": ["pyproject.toml", "setup.cfg", "tox.ini"], "content_patterns": [r"\[tool\.pytest", r"\[pytest\]"]},
    {"name": "jest", "category": "Testing", "filenames": ["jest.config.js", "jest.config.ts", "jest.config.mjs", "jest.config.json", "jest.config.cjs"], "content_files": ["package.json"], "content_patterns": [r'"jest"\s*:', r'"@jest/', r'"jest-circus"']},
    {"name": "mocha", "category": "Testing", "filenames": [".mocharc.yml", ".mocharc.yaml", ".mocharc.js", ".mocharc.json", ".mocharc.cjs"], "content_files": ["package.json"], "content_patterns": [r'"mocha"']},
    {"name": "vitest", "category": "Testing", "filenames": ["vitest.config.ts", "vitest.config.js", "vitest.config.mjs"], "content_files": ["package.json"], "content_patterns": [r'"vitest"']},
    {"name": "playwright", "category": "Testing", "filenames": ["playwright.config.ts", "playwright.config.js", "playwright.config.mjs"], "content_files": ["package.json"], "content_patterns": [r'"@playwright/', r'"playwright"']},
    {"name": "cypress", "category": "Testing", "filenames": ["cypress.config.ts", "cypress.config.js", "cypress.config.mjs", "cypress.json"], "content_files": ["package.json"], "content_patterns": [r'"cypress"']},
    {"name": "rspec", "category": "Testing", "filenames": [".rspec"], "content_files": ["Gemfile"], "content_patterns": [r'rspec']},
    {"name": "junit", "category": "Testing", "content_files": ["pom.xml", "build.gradle", "build.gradle.kts"], "content_patterns": [r'junit', r'JUnit']},
    {"name": "robot framework", "category": "Testing", "filenames": ["robot.yaml"], "content_files": ["pyproject.toml", "requirements.txt"], "content_patterns": [r'robotframework']},
    {"name": "selenium", "category": "Testing", "content_files": ["pyproject.toml", "requirements.txt", "package.json"], "content_patterns": [r'selenium']},

    # === Linting & Formatting ===
    {"name": "ESLint", "category": "Linting", "filenames": [".eslintrc.js", ".eslintrc.cjs", ".eslintrc.yaml", ".eslintrc.yml", ".eslintrc.json", ".eslintrc", "eslint.config.js", "eslint.config.mjs"], "content_files": ["package.json"], "content_patterns": [r'"eslint"']},
    {"name": "Prettier", "category": "Linting", "filenames": [".prettierrc", ".prettierrc.json", ".prettierrc.yaml", ".prettierrc.yml", ".prettierrc.js", ".prettierrc.cjs", "prettier.config.js", ".prettierrc.toml"], "content_files": ["package.json"], "content_patterns": [r'"prettier"']},
    {"name": "Ruff", "category": "Linting", "content_files": ["pyproject.toml", ".ruff.toml", "ruff.toml"], "content_patterns": [r"\[tool\.ruff", r"\[ruff\]"]},
    {"name": "Black", "category": "Linting", "content_files": ["pyproject.toml", "setup.cfg", ".black"], "content_patterns": [r"\[tool\.black", r"\[black\]"]},
    {"name": "Flake8", "category": "Linting", "filenames": [".flake8"], "content_files": ["setup.cfg", "tox.ini"], "content_patterns": [r"\[flake8\]"]},
    {"name": "isort", "category": "Linting", "filenames": [".isort.cfg"], "content_files": ["pyproject.toml", "setup.cfg"], "content_patterns": [r"\[tool\.isort", r"\[isort\]"]},
    {"name": "MyPy", "category": "Linting", "filenames": ["mypy.ini", ".mypy.ini"], "content_files": ["pyproject.toml", "setup.cfg"], "content_patterns": [r"\[tool\.mypy", r"\[mypy\]"]},
    {"name": "Pylint", "category": "Linting", "filenames": [".pylintrc", "pylintrc"], "content_files": ["pyproject.toml", "setup.cfg"], "content_patterns": [r"\[tool\.pylint", r"\[pylint\]"]},
    {"name": "RuboCop", "category": "Linting", "filenames": [".rubocop.yml", ".rubocop.yaml", ".rubocop_todo.yml"]},
    {"name": "Clippy", "category": "Linting", "filenames": ["clippy.toml", ".clippy.toml"]},
    {"name": "Golangci-lint", "category": "Linting", "filenames": [".golangci.yml", ".golangci.yaml", ".golangci.toml"]},

    # === Build Systems ===
    {"name": "Webpack", "category": "Build", "filenames": ["webpack.config.js", "webpack.config.ts", "webpack.config.mjs", "webpack.config.cjs", "webpack.common.js"]},
    {"name": "Vite", "category": "Build", "filenames": ["vite.config.ts", "vite.config.js", "vite.config.mjs"]},
    {"name": "esbuild", "category": "Build", "filenames": ["esbuild.config.js", "esbuild.config.mjs", "esbuild.config.ts"], "content_files": ["package.json"], "content_patterns": [r'"esbuild"']},
    {"name": "Rollup", "category": "Build", "filenames": ["rollup.config.js", "rollup.config.ts", "rollup.config.mjs"]},
    {"name": "Parcel", "category": "Build", "filenames": [".parcelrc"]},
    {"name": "Make", "category": "Build", "filenames": ["Makefile", "makefile", "GNUmakefile"]},
    {"name": "CMake", "category": "Build", "filenames": ["CMakeLists.txt", "cmake/"]},
    {"name": "Bazel", "category": "Build", "filenames": ["BUILD", "BUILD.bazel", "WORKSPACE", "WORKSPACE.bazel"]},
    {"name": "Meson", "category": "Build", "filenames": ["meson.build", "meson_options.txt"]},
    {"name": "Gradle", "category": "Build", "filenames": ["build.gradle", "build.gradle.kts", "gradlew", "gradlew.bat", "settings.gradle", "settings.gradle.kts"]},
    {"name": "Maven", "category": "Build", "filenames": ["pom.xml", "mvnw", "mvnw.cmd"]},
    {"name": "Cargo", "category": "Build", "filenames": ["Cargo.toml"]},
    {"name": "TSC", "category": "Build", "filenames": ["tsconfig.json", "tsconfig.build.json", "tsconfig.base.json"]},
    {"name": "Babel", "category": "Build", "filenames": ["babel.config.js", "babel.config.cjs", "babel.config.mjs", "babel.config.json", ".babelrc", ".babelrc.json", ".babelrc.js"]},
    {"name": "swc", "category": "Build", "filenames": [".swcrc", "swc.config.js"]},
    {"name": "Sass", "category": "Build", "filenames": [".sassrc", ".sassrc.js"], "content_files": ["package.json"], "content_patterns": [r'"sass"', r'"node-sass"']},
    {"name": "PostCSS", "category": "Build", "filenames": ["postcss.config.js", "postcss.config.cjs", "postcss.config.mjs", ".postcssrc", ".postcssrc.json"]},
    {"name": "Tailwind CSS", "category": "Build", "filenames": ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs", "tailwind.config.mjs"]},

    # === Documentation ===
    {"name": "Sphinx", "category": "Documentation", "filenames": ["conf.py", "docs/conf.py"], "content_files": ["pyproject.toml", "docs/requirements.txt"], "content_patterns": [r'sphinx']},
    {"name": "MkDocs", "category": "Documentation", "filenames": ["mkdocs.yml", "mkdocs.yaml"]},
    {"name": "JSDoc", "category": "Documentation", "filenames": ["jsdoc.json", "jsdoc.config.json", ".jsdocrc"], "content_files": ["package.json"], "content_patterns": [r'"jsdoc"']},
    {"name": "TypeDoc", "category": "Documentation", "filenames": ["typedoc.json", "typedoc.config.js", "typedoc.config.ts"], "content_files": ["package.json"], "content_patterns": [r'"typedoc"']},
    {"name": "Storybook", "category": "Documentation", "filenames": [".storybook/", "main.js|.storybook"], "content_files": ["package.json"], "content_patterns": [r'"@storybook/']},

    # === Containers ===
    {"name": "Docker", "category": "Containers", "filenames": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "docker-compose.override.yml", ".dockerignore", "Dockerfile.*"]},
    {"name": "Kubernetes", "category": "Containers", "filenames": ["kustomization.yaml", "kustomization.yml", "Chart.yaml"]},
    {"name": "Helm", "category": "Containers", "filenames": ["Chart.yaml", "values.yaml", "values.production.yaml"]},
    {"name": "Podman", "category": "Containers", "filenames": ["Containerfile", "containers.conf"]},

    # === Database ===
    {"name": "Prisma", "category": "Database", "filenames": ["schema.prisma"]},
    {"name": "Alembic", "category": "Database", "filenames": ["alembic.ini"], "content_files": ["pyproject.toml", "requirements.txt"], "content_patterns": [r'alembic']},
    {"name": "Flyway", "category": "Database", "filenames": ["flyway.conf", "flyway.toml"]},
    {"name": "Liquibase", "category": "Database", "filenames": ["liquibase.properties", "db/changelog/"]},
    {"name": "Sequelize", "category": "Database", "content_files": ["package.json"], "content_patterns": [r'"sequelize"']},
    {"name": "TypeORM", "category": "Database", "content_files": ["package.json"], "content_patterns": [r'"typeorm"']},
    {"name": "Drizzle", "category": "Database", "content_files": ["package.json"], "content_patterns": [r'"drizzle-orm"']},
    {"name": "Redis", "category": "Database", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "Gemfile", "Cargo.toml", "go.mod"], "content_patterns": [r'redis']},
    {"name": "MongoDB", "category": "Database", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "Gemfile"], "content_patterns": [r'pymongo', r'mongoose', r'mongodb', r'mongo']},
    {"name": "PostgreSQL", "category": "Database", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "Gemfile", "Cargo.toml", "go.mod"], "content_patterns": [r'psycopg', r'pg\b', r'postgres']},

    # === Message Queues ===
    {"name": "Celery", "category": "Messaging", "content_files": ["pyproject.toml", "requirements.txt", "setup.cfg"], "content_patterns": [r'celery']},
    {"name": "RabbitMQ", "category": "Messaging", "content_files": ["pyproject.toml", "requirements.txt", "package.json"], "content_patterns": [r'pika', r'amqp', r'rabbitmq', r'amqplib']},
    {"name": "Kafka", "category": "Messaging", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "go.mod"], "content_patterns": [r'kafka', r'confluent-kafka']},
    {"name": "NATS", "category": "Messaging", "content_files": ["package.json", "go.mod", "Cargo.toml"], "content_patterns": [r'nats']},

    # === Monitoring ===
    {"name": "Sentry", "category": "Monitoring", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "Gemfile"], "content_patterns": [r'sentry-sdk', r'@sentry/', r'sentry-raven', r'sentry-ruby']},
    {"name": "Datadog", "category": "Monitoring", "content_files": ["pyproject.toml", "requirements.txt", "package.json"], "content_patterns": [r'ddtrace', r'datadog']},
    {"name": "Prometheus", "category": "Monitoring", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "go.mod"], "content_patterns": [r'prometheus', r'prometheus_client']},
    {"name": "OpenTelemetry", "category": "Monitoring", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "go.mod"], "content_patterns": [r'opentelemetry']},
    {"name": "New Relic", "category": "Monitoring", "content_files": ["pyproject.toml", "requirements.txt", "package.json"], "content_patterns": [r'newrelic']},
    {"name": "Grafana", "category": "Monitoring", "filenames": ["grafana.ini", "dashboards/"]},
    {"name": "Logstash", "category": "Monitoring", "filenames": ["logstash.conf"]},

    # === Cloud ===
    {"name": "AWS", "category": "Cloud", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "go.mod"], "content_patterns": [r'boto3', r'aws-sdk', r'aws-sam']},
    {"name": "Terraform", "category": "Cloud", "filenames": ["*.tf", "*.tfvars", ".terraform.lock.hcl"]},
    {"name": "Pulumi", "category": "Cloud", "filenames": ["Pulumi.yaml", "Pulumi.dev.yaml", "Pulumi.prod.yaml"]},
    {"name": "Serverless", "category": "Cloud", "filenames": ["serverless.yml", "serverless.yaml", "serverless.json"]},
    {"name": "Google Cloud", "category": "Cloud", "content_files": ["pyproject.toml", "requirements.txt", "package.json", "go.mod"], "content_patterns": [r'google-cloud']},
    {"name": "Azure", "category": "Cloud", "content_files": ["pyproject.toml", "requirements.txt", "package.json"], "content_patterns": [r'azure-']},

    # === Git Hooks & Automation ===
    {"name": "Pre-commit", "category": "Automation", "filenames": [".pre-commit-config.yaml", ".pre-commit-hooks.yaml"]},
    {"name": "Husky", "category": "Automation", "filenames": [".husky/"]},
    {"name": "Commitlint", "category": "Automation", "filenames": ["commitlint.config.js", "commitlint.config.cjs", ".commitlintrc.json", ".commitlintrc.yaml"]},
    {"name": "Semantic Release", "category": "Automation", "filenames": [".releaserc.json", ".releaserc.yaml", ".releaserc.js", "release.config.js"]},
    {"name": "Dependabot", "category": "Automation", "filenames": [".github/dependabot.yml", ".github/dependabot.yaml"]},
    {"name": "Renovate", "category": "Automation", "filenames": ["renovate.json", "renovate.json5", ".github/renovate.json"]},
    {"name": "Lint-staged", "category": "Automation", "content_files": ["package.json", ".lintstagedrc.js", ".lintstagedrc.json", ".lintstagedrc.yaml"], "content_patterns": [r'"lint-staged"']},

    # === Utilities ===
    {"name": "EditorConfig", "category": "Utilities", "filenames": [".editorconfig"]},
    {"name": "pyenv", "category": "Utilities", "filenames": [".python-version", ".python-version"]},
    {"name": "nvm / fnm", "category": "Utilities", "filenames": [".nvmrc", ".node-version"]},
    {"name": "rustup", "category": "Utilities", "filenames": ["rust-toolchain.toml", "rust-toolchain"]},
    {"name": "asdf", "category": "Utilities", "filenames": [".tool-versions"]},
    {"name": "direnv", "category": "Utilities", "filenames": [".envrc", ".envrc"]},
    {"name": "Poetry", "category": "Build", "filenames": ["poetry.lock"], "content_files": ["pyproject.toml"], "content_patterns": [r'\[tool\.poetry\]']},
    {"name": "Pipenv", "category": "Build", "filenames": ["Pipfile", "Pipfile.lock"]},
    {"name": "Yarn", "category": "Build", "filenames": ["yarn.lock", ".yarnrc.yml", ".yarnrc"]},
    {"name": "pnpm", "category": "Build", "filenames": ["pnpm-lock.yaml", "pnpm-workspace.yaml"]},
    {"name": "npm", "category": "Build", "filenames": ["package-lock.json", "package.json"]},

    # === Frameworks (web / api) ===
    {"name": "Flask", "category": "Frameworks", "content_files": ["pyproject.toml", "requirements.txt", "setup.cfg"], "content_patterns": [r'flask']},
    {"name": "FastAPI", "category": "Frameworks", "content_files": ["pyproject.toml", "requirements.txt"], "content_patterns": [r'fastapi']},
    {"name": "Django", "category": "Frameworks", "content_files": ["pyproject.toml", "requirements.txt", "setup.cfg"], "content_patterns": [r'django']},
    {"name": "Express", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"express"']},
    {"name": "Next.js", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"next"']},
    {"name": "Nuxt.js", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"nuxt"']},
    {"name": "React", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"react"', r'"react-dom"']},
    {"name": "Vue.js", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"vue"']},
    {"name": "Angular", "category": "Frameworks", "content_files": ["package.json"], "content_patterns": [r'"@angular/core"']},
    {"name": "Svelte", "category": "Frameworks", "content_files": ["package.json", "svelte.config.js"], "content_patterns": [r'"svelte"']},
    {"name": "Ruby on Rails", "category": "Frameworks", "filenames": ["Gemfile"], "content_patterns": [r'rails']},
    {"name": "Spring Boot", "category": "Frameworks", "filenames": ["pom.xml", "build.gradle", "build.gradle.kts"], "content_patterns": [r'spring-boot', r'org\.springframework']},
    {"name": "Actix-web", "category": "Frameworks", "content_files": ["Cargo.toml"], "content_patterns": [r'actix-web']},
    {"name": "Axum", "category": "Frameworks", "content_files": ["Cargo.toml"], "content_patterns": [r'axum']},
    {"name": "Gin", "category": "Frameworks", "content_files": ["go.mod"], "content_patterns": [r'gin-gonic']},
    {"name": "Echo", "category": "Frameworks", "content_files": ["go.mod"], "content_patterns": [r'echo']},
    {"name": "Fiber", "category": "Frameworks", "content_files": ["go.mod"], "content_patterns": [r'fiber']},

    # === Mobile ===
    {"name": "React Native", "category": "Mobile", "content_files": ["package.json"], "content_patterns": [r'"react-native"']},
    {"name": "Flutter", "category": "Mobile", "filenames": ["pubspec.yaml"]},
    {"name": "Expo", "category": "Mobile", "content_files": ["package.json", "app.json", "app.config.js"], "content_patterns": [r'"expo"']},
    {"name": "SwiftUI", "category": "Mobile", "filenames": ["*.swift"]},
    {"name": "Kotlin Multiplatform", "category": "Mobile", "filenames": ["build.gradle.kts"]},

    # === Languages ===
    {"name": "Python", "category": "Languages", "filenames": ["requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile"]},
    {"name": "JavaScript", "category": "Languages", "filenames": ["package.json", "package-lock.json"]},
    {"name": "TypeScript", "category": "Languages", "filenames": ["tsconfig.json", "tsconfig.build.json"]},
    {"name": "Rust", "category": "Languages", "filenames": ["Cargo.toml", "Cargo.lock", "rust-toolchain.toml"]},
    {"name": "Go", "category": "Languages", "filenames": ["go.mod", "go.sum"]},
    {"name": "Ruby", "category": "Languages", "filenames": ["Gemfile", "Gemfile.lock", ".ruby-version"]},
    {"name": "Java", "category": "Languages", "filenames": ["pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle"]},
    {"name": "Kotlin", "category": "Languages", "filenames": ["build.gradle.kts"]},
    {"name": "Swift", "category": "Languages", "filenames": ["Package.swift"]},
    {"name": "PHP", "category": "Languages", "filenames": ["composer.json", "composer.lock"]},
]

CATEGORY_FILE_PATTERNS: dict[str, list[str]] = {
    "readme": ["readme", "read_me"],
    "license": ["license", "licence", "copying"],
    "changelog": ["changelog", "changes", "history", "releases"],
    "contributing": ["contributing", "contribute"],
    "code_of_conduct": ["code_of_conduct", "conduct"],
    "security_policy": ["security.md", "security"],
    "entrypoint": ["main.py", "app.py", "cli.py", "run.py", "server.py", "manage.py",
                    "index.js", "main.js", "app.js", "server.js",
                    "main.go", "cmd/main.go",
                    "main.rs", "src/main.rs"],
    "env": [".env", ".env.example", ".env.production", ".env.development", ".env.local"],
    "git": [".gitignore", ".gitattributes", ".gitmodules", ".gitkeep"],
    "editor": [".editorconfig", ".vscode/", ".idea/"],
    "ci": [".github/workflows", ".gitlab-ci", ".circleci", ".travis.yml", "azure-pipelines", "jenkinsfile"],
}

_KEY_CONFIG_CACHE: dict[str, tuple[dict | None, str | None]] = {}


def _parse_toml_simple(text: str) -> dict | None:
    result: dict = {}
    current_section: str = ""
    for line in text.split("\n"):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        sec_match = re.match(r"^\[([^\]]+)\]\s*$", line_stripped)
        if sec_match:
            current_section = sec_match.group(1)
            result[current_section] = {}
            continue
        kv_match = re.match(r'^([^=#]+?)\s*=\s*(.+)$', line_stripped)
        if kv_match:
            key = kv_match.group(1).strip()
            val = kv_match.group(2).strip().strip('"').strip("'")
            if current_section:
                result[current_section][key] = val
            else:
                result[key] = val
    if current_section:
        return result
    return result if result else None


def _extract_versions_from_pyproject(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    # Array-style: dependencies = ["flask>=2.3.0", "pytest>=7.0.0"]
    for match in re.finditer(r'\[([^\]]*)\]', content):
        inner = match.group(1)
        for item in re.finditer(r'"([^"]+)"', inner):
            dep = item.group(1)
            parts = dep.split("[", 1)[0].split(";", 1)[0].strip()
            ver_match = re.search(r'([><=!~]+\s*[\d.*]+)', dep)
            ver = ver_match.group(1).strip() if ver_match else ""
            pkg = re.split(r"[><=!~]+", parts, maxsplit=1)[0].strip()
            if pkg and pkg not in ("python", "pip"):
                versions[pkg.lower()] = ver
    # Inline deps (old-style setup.cfg format)
    deps = re.findall(r'^\s*["\']([^"\']+)["\']\s*(?:$|,)', content, re.MULTILINE)
    for dep in deps:
        parts = dep.split("[", 1)[0].split(";", 1)[0].strip()
        ver_match = re.search(r'([><=!~]+\s*[\d.*]+)', dep)
        ver = ver_match.group(1).strip() if ver_match else ""
        pkg = re.split(r"[><=!~]+", parts, maxsplit=1)[0].strip()
        if pkg and pkg not in ("python", "pip"):
            versions[pkg.lower()] = ver
    return versions


def _extract_versions_from_requirements(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        parts = re.split(r"[><=!~]+", line, maxsplit=1)
        pkg_name = parts[0].strip().lower().replace("_", "-").replace(".", "-")
        ver = ""
        if len(parts) > 1:
            ver_match = re.search(r"([><=!~]+\s*[\d.*]+)", line)
            if ver_match:
                ver = ver_match.group(1).strip()
        if pkg_name:
            versions[pkg_name] = ver
    return versions


def _extract_versions_from_gemfile(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    for match in re.finditer(r"^\s*gem\s+['\"]([^'\"]+)['\"]", content, re.MULTILINE):
        name = match.group(1).lower()
        versions[name] = ""
    return versions


def _extract_versions_from_cargo(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    in_deps = False
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[dependencies"):
            in_deps = True
            continue
        if in_deps and stripped.startswith("["):
            in_deps = False
            continue
        if in_deps and "=" in stripped:
            parts = stripped.split("=", 1)
            name = parts[0].strip()
            ver = parts[1].strip().strip('"').strip("'").strip(",")
            if name and name not in ("true", "false"):
                versions[name.lower()] = ver
    return versions


def _extract_versions_from_gomod(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    for match in re.finditer(r"^\s+([^\s]+)\s+v?([\d.]+)", content, re.MULTILINE):
        name = match.group(1).lower()
        ver = match.group(2)
        if name not in ("go", "require"):
            versions[name] = ver
    return versions


_VERSION_EXTRACTORS: dict[str, callable] = {
    "pyproject.toml": _extract_versions_from_pyproject,
    "setup.cfg": _extract_versions_from_pyproject,
    "requirements.txt": _extract_versions_from_requirements,
    "Gemfile": _extract_versions_from_gemfile,
    "Cargo.toml": _extract_versions_from_cargo,
    "go.mod": _extract_versions_from_gomod,
}


def _extract_versions_from_package_json(content: str) -> dict[str, str]:
    versions: dict[str, str] = {}
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return versions
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            for name, ver in deps.items():
                versions[name.lower()] = str(ver)
    return versions


def _detect_tools_from_files(files: list[FileInfo]) -> dict[str, list[DetectedTool]]:
    from collections import defaultdict

    tools_by_cat: dict[str, list[DetectedTool]] = defaultdict(list)
    found: set[str] = set()

    file_map: dict[str, list[tuple[Path, str]]] = {}
    for f in files:
        rel = f.relative_path
        name = rel.name.lower()
        path_str = rel.as_posix()
        file_map.setdefault(name, []).append((rel, path_str))

    for f in files:
        rel = f.relative_path
        name = rel.name.lower()
        path_str = rel.as_posix()
        if f.is_binary:
            continue
        content = read_text(f.path)

        for td in _TOOL_DEFS:
            tname = td["name"].lower()
            if tname in found:
                continue

            # Filename match (exact or glob)
            matched = False
            for fn in td.get("filenames", []):
                fn_lower = fn.lower()
                if fn_lower.endswith("/*"):
                    dir_name = fn_lower.replace("/*", "")
                    if dir_name in path_str:
                        matched = True
                        break
                elif fn_lower.startswith("*."):
                    ext = fn_lower.replace("*.", ".")
                    if name.endswith(ext) or f.relative_path.suffix == ext:
                        matched = True
                        break
                elif fn_lower == name or fn_lower in path_str:
                    matched = True
                    break
            if matched:
                version = _try_extract_version(td, file_map, content)
                tools_by_cat[td["category"]].append(DetectedTool(
                    name=td["name"],
                    version=version,
                    config_file=path_str,
                    category=td["category"],
                ))
                found.add(tname)
                continue

            # Content match
            if content and not matched:
                for cf in td.get("content_files", []):
                    if name == cf.lower() or path_str.endswith(cf):
                        for pat in td.get("content_patterns", []):
                            if re.search(pat, content, re.IGNORECASE):
                                version = _try_extract_version(td, file_map, content)
                                tools_by_cat[td["category"]].append(DetectedTool(
                                    name=td["name"],
                                    version=version,
                                    config_file=path_str,
                                    category=td["category"],
                                ))
                                found.add(tname)
                                matched = True
                                break
                    if matched:
                        break

    return dict(tools_by_cat)


def _try_extract_version(td: dict, file_map: dict, current_content: str) -> str | None:
    tname = td["name"].lower()
    for cf in td.get("content_files", []):
        # Check if we've already parsed this file
        if cf in _KEY_CONFIG_CACHE:
            parsed, _ = _KEY_CONFIG_CACHE[cf]
        else:
            content = None
            if cf in file_map:
                for rel, path_str in file_map[cf]:
                    content = read_text(rel if rel.exists() else Path(path_str))
                    break
            parsed = None
            if content:
                if cf == "package.json":
                    parsed = _extract_versions_from_package_json(content)
                elif cf in _VERSION_EXTRACTORS:
                    parsed = _VERSION_EXTRACTORS[cf](content)
            _KEY_CONFIG_CACHE[cf] = (parsed, None)

        if parsed and isinstance(parsed, dict):
            for pkg_name, ver in parsed.items():
                pkg_lower = pkg_name.lower()
                if tname in pkg_lower or pkg_lower in tname:
                    if ver:
                        return ver
    return None


def _build_file_categories(files: list[FileInfo]) -> dict[str, list[Path]]:
    categories: dict[str, list[Path]] = {k: [] for k in CATEGORY_FILE_PATTERNS}
    for f in files:
        rel = f.relative_path
        name_lower = rel.name.lower()
        path_str = rel.as_posix().lower()
        for cat, patterns in CATEGORY_FILE_PATTERNS.items():
            if any(p in name_lower or p in path_str for p in patterns):
                categories[cat].append(rel)
                break
    return {k: v for k, v in categories.items() if v}


class ProjectIntelligenceExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> ProjectIntelligenceResult:
        _KEY_CONFIG_CACHE.clear()
        tools = _detect_tools_from_files(files)
        categories = _build_file_categories(files)
        return ProjectIntelligenceResult(tools=tools, categories=categories)
