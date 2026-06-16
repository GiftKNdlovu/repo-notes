"""README.md generator."""

from pathlib import Path

from repo_notes.extractors import (
    ApiEndpointResult,
    ArchitectureResult,
    CicdResult,
    ComplexityResult,
    DatabaseResult,
    DependenciesResult,
    ProjectIntelligenceResult,
    ScriptsResult,
    StatsResult,
    TypeCoverageResult,
)
from repo_notes.extractors.readme_data import ReadmeData


class ReadmeGenerator:
    def __init__(self, root: Path):
        self.root = root

    def generate(
        self,
        readme_data: ReadmeData,
        stats: StatsResult | None = None,
        project_intelligence: ProjectIntelligenceResult | None = None,
        scripts: ScriptsResult | None = None,
        arch: ArchitectureResult | None = None,
        deps: DependenciesResult | None = None,
        cicd: CicdResult | None = None,
        type_coverage: TypeCoverageResult | None = None,
        complexity: ComplexityResult | None = None,
        api_endpoints: ApiEndpointResult | None = None,
        database: DatabaseResult | None = None,
        **_unused,
    ) -> str:
        sections = [
            self._render_header(readme_data),
            self._render_badges(readme_data),
            self._render_overview(readme_data, project_intelligence, stats),
            self._render_features(readme_data, project_intelligence, api_endpoints, database),
            self._render_tech_stack(project_intelligence, deps),
            self._render_quick_start(readme_data),
            self._render_usage(readme_data, scripts),
            self._render_commands(project_intelligence, scripts),
            self._render_project_structure(arch, project_intelligence),
        ]

        if stats:
            sections.append(self._render_stats(stats))

        sections.append(
            self._render_development(
                readme_data,
                project_intelligence=project_intelligence,
                scripts=scripts,
            )
        )
        sections.append(
            self._render_quality_notes(
                readme_data,
                cicd=cicd,
                type_coverage=type_coverage,
                complexity=complexity,
                api_endpoints=api_endpoints,
                database=database,
            )
        )
        sections.append(self._render_license(readme_data))

        return "\n\n".join(s.rstrip() for s in sections if s.strip()) + "\n"

    def _render_header(self, data: ReadmeData) -> str:
        lines = [f"# {data.name}"]
        if data.description:
            lines.append("")
            lines.append(data.description)
        return "\n".join(lines)

    def _render_badges(self, data: ReadmeData) -> str:
        parts = []
        if data.version:
            parts.append(f"![Version](https://img.shields.io/badge/version-{data.version}-blue)")
        if data.license_type:
            license_encoded = data.license_type.replace("-", "--").replace(" ", "%20")
            parts.append(f"![License](https://img.shields.io/badge/license-{license_encoded}-green)")
        if data.python_requires:
            py_encoded = data.python_requires.replace(">=", "%3E%3D").replace(" ", "%20")
            parts.append(f"![Python](https://img.shields.io/badge/python-{py_encoded}-yellow)")
        if data.ci_provider:
            ci_name = data.ci_provider.lower().replace(" ", "_")
            parts.append(f"![CI](https://img.shields.io/badge/ci-{ci_name}-orange)")
        if data.has_tests:
            parts.append("![Tests](https://img.shields.io/badge/tests-passing-brightgreen)")
        return " ".join(parts) if parts else ""

    def _render_overview(
        self,
        data: ReadmeData,
        project_intelligence: ProjectIntelligenceResult | None,
        stats: StatsResult | None,
    ) -> str:
        lines = ["## Overview", ""]
        if data.description:
            lines.append(data.description)
        else:
            lines.append(f"{data.name} is a software project generated from repository metadata.")
        if project_intelligence and project_intelligence.total_tools:
            tools = ", ".join(self._tool_names(project_intelligence, limit=6))
            lines.append("")
            lines.append(f"Detected stack highlights include {tools}.")
        if stats:
            lines.append("")
            lines.append(
                f"The repository contains {stats.total_files} files and "
                f"{stats.total_lines:,} lines of code."
            )
        return "\n".join(lines)

    def _render_quick_start(self, data: ReadmeData) -> str:
        lines = ["## Quick Start", ""]
        if data.install_cmd:
            lines.append("```bash")
            lines.append(data.install_cmd)
            lines.append("```")
        else:
            lines.append("Installation command could not be detected.")
        return "\n".join(lines)

    def _render_features(
        self,
        data: ReadmeData,
        project_intelligence: ProjectIntelligenceResult | None,
        api_endpoints: ApiEndpointResult | None,
        database: DatabaseResult | None,
    ) -> str:
        lines = ["## Features", ""]
        if data.runtime_deps:
            deps = ", ".join(data.runtime_deps[:8])
            suffix = f" and {len(data.runtime_deps) - 8} more" if len(data.runtime_deps) > 8 else ""
            lines.append(f"- **{len(data.runtime_deps)} runtime dependencies** - {deps}{suffix}")
        if project_intelligence and project_intelligence.total_tools:
            lines.append(
                f"- **Tool detection** - {project_intelligence.total_tools} tools across "
                f"{project_intelligence.total_categories} categories"
            )
        if api_endpoints and api_endpoints.endpoints:
            real = [e for e in api_endpoints.endpoints if not self._is_test_path(e.get("file", ""))]
            if real:
                lines.append(f"- **API routes** - {len(real)} endpoint patterns detected")
        if database and (database.model_files or database.migration_files):
            real_files = [
                p.as_posix()
                for p in database.model_files + database.migration_files
                if not self._is_test_path(p.as_posix())
            ]
            if real_files:
                lines.append("- **Database support** - models or migrations detected")
        if data.has_tests:
            lines.append("- **Test suite** - ready for development")
        if data.has_ci:
            lines.append(f"- **CI configured** - {data.ci_provider}")
        if data.has_docker:
            lines.append("- **Docker support** - containerized development")
        if len(lines) == 2:
            lines.append("- Repository metadata is available for project onboarding.")
        return "\n".join(lines)

    def _render_tech_stack(
        self,
        project_intelligence: ProjectIntelligenceResult | None,
        deps: DependenciesResult | None,
    ) -> str:
        lines = ["## Tech Stack", ""]
        wrote = False
        if project_intelligence and project_intelligence.tools:
            for category in (
                "Languages",
                "Frameworks",
                "Build",
                "Testing",
                "Linting",
                "Database",
                "Containers",
                "Mobile",
            ):
                tools = project_intelligence.tools.get(category)
                if not tools:
                    continue
                values = ", ".join(self._format_tool(tool) for tool in tools[:8])
                lines.append(f"- **{category}**: {values}")
                wrote = True
        if deps:
            manifests = self._dependency_manifests(deps)
            if manifests:
                lines.append(f"- **Dependency manifests**: {', '.join(f'`{m}`' for m in manifests)}")
                wrote = True
        if not wrote:
            lines.append("- No framework or tool metadata was detected.")
        return "\n".join(lines)

    def _render_usage(self, data: ReadmeData, scripts: ScriptsResult | None = None) -> str:
        lines = ["## Usage", ""]
        console_scripts = sorted(scripts.pyproject_scripts) if scripts and scripts.pyproject_scripts else []
        command_name = console_scripts[0] if console_scripts else data.name
        lines.append("```bash")
        lines.append(f"{command_name} [OPTIONS] [PATH]")
        lines.append("```")
        return "\n".join(lines)

    def _render_commands(
        self,
        project_intelligence: ProjectIntelligenceResult | None,
        scripts: ScriptsResult | None,
    ) -> str:
        commands = self._commands(project_intelligence, scripts)
        lines = ["## Commands", ""]
        if commands:
            lines.append("| Task | Command |")
            lines.append("|------|---------|")
            for label, command in commands:
                lines.append(f"| {label} | `{command}` |")
        else:
            lines.append("No common project commands were detected.")
        return "\n".join(lines)

    def _render_project_structure(
        self,
        arch: ArchitectureResult | None,
        project_intelligence: ProjectIntelligenceResult | None,
    ) -> str:
        paths: list[tuple[str, str]] = []
        if arch:
            for path in arch.entry_points[:5]:
                paths.append((path.as_posix(), "Entry point"))
            for layer, layer_paths in sorted(arch.layers.items()):
                for path in layer_paths[:2]:
                    paths.append((path.as_posix(), f"{layer.title()} layer"))
        if project_intelligence:
            for category, label in (
                ("readme", "Documentation"),
                ("ci", "CI configuration"),
                ("env", "Environment file"),
                ("license", "License"),
            ):
                for path in project_intelligence.categories.get(category, [])[:3]:
                    paths.append((path.as_posix(), label))

        lines = ["## Project Structure", ""]
        unique = self._unique_pairs(paths)
        if unique:
            lines.append("| Path | Purpose |")
            lines.append("|------|---------|")
            for path, purpose in unique[:12]:
                lines.append(f"| `{path}` | {purpose} |")
        else:
            lines.append("No high-signal project paths were detected.")
        return "\n".join(lines)

    def _render_stats(self, result: StatsResult) -> str:
        lines = ["## Code Statistics", ""]
        lines.append(f"- **Total files**: {result.total_files}")
        lines.append(f"- **Total lines**: {result.total_lines:,}")
        if result.by_language:
            lang_summary = ", ".join(
                f"{lang}: {data['files']} files, {data['lines']} lines"
                for lang, data in sorted(result.by_language.items(), key=lambda x: -x[1]["lines"])
            )
            lines.append(f"- **Languages**: {lang_summary}")
        if result.largest_files:
            largest = ", ".join(f"`{path.as_posix()}`" for path, _lines in result.largest_files[:3])
            lines.append(f"- **Largest files**: {largest}")
        return "\n".join(lines)

    def _render_development(
        self,
        data: ReadmeData,
        project_intelligence: ProjectIntelligenceResult | None = None,
        scripts: ScriptsResult | None = None,
    ) -> str:
        lines = ["## Development", ""]
        if data.dev_install_cmd:
            lines.append("```bash")
            lines.append(data.dev_install_cmd)
            lines.append("```")
            lines.append("")

        commands = self._commands(project_intelligence, scripts)
        if commands:
            lines.append("Common development commands:")
            lines.append("")
            lines.append("```bash")
            for label, command in commands[:6]:
                lines.append(f"# {label}")
                lines.append(command)
                lines.append("")
            if lines[-1] == "":
                lines.pop()
            lines.append("```")
        else:
            lines.append("No test, lint, or build commands were detected.")
        return "\n".join(lines)

    def _render_quality_notes(
        self,
        data: ReadmeData,
        cicd: CicdResult | None,
        type_coverage: TypeCoverageResult | None,
        complexity: ComplexityResult | None,
        api_endpoints: ApiEndpointResult | None,
        database: DatabaseResult | None,
    ) -> str:
        lines = ["## Quality Notes", ""]
        notes = []
        if data.has_tests:
            notes.append("Tests were detected in the repository.")
        if cicd and self._has_ci(cicd):
            notes.append("CI/CD configuration was detected.")
        elif data.has_ci:
            notes.append(f"CI/CD configuration was detected via {data.ci_provider}.")
        if type_coverage:
            total_files = type_coverage.typed_files + type_coverage.untyped_files
            if total_files:
                pct = (type_coverage.typed_files / total_files) * 100
                notes.append(f"Estimated type coverage: {pct:.1f}% of files typed.")
        if complexity and complexity.complex_files:
            files = ", ".join(f"`{item['file']}`" for item in complexity.complex_files[:3])
            notes.append(f"Complexity hot spots include {files}.")
        if api_endpoints and api_endpoints.endpoints:
            files = [e.get("file", "") for e in api_endpoints.endpoints]
            if files and all(self._is_test_path(path) for path in files):
                notes.append("API endpoint patterns appear only in tests.")
        if database:
            db_files = [p.as_posix() for p in database.model_files + database.migration_files]
            if db_files and all(self._is_test_path(path) for path in db_files):
                notes.append("Database/ORM signals appear only in tests.")

        if notes:
            lines.extend(f"- {note}" for note in notes)
        else:
            lines.append("No specific quality signals were detected.")
        return "\n".join(lines)

    def _render_license(self, data: ReadmeData) -> str:
        if data.license_type:
            return f"## License\n\n{data.license_type}"
        return "## License\n\nMIT"

    def _tool_names(self, result: ProjectIntelligenceResult, limit: int) -> list[str]:
        names: list[str] = []
        for category in ("Languages", "Frameworks", "Build", "Testing", "Linting", "Mobile"):
            names.extend(tool.name for tool in result.tools.get(category, []))
        return list(dict.fromkeys(names))[:limit]

    def _format_tool(self, tool) -> str:
        if tool.version:
            return f"{tool.name} ({tool.version})"
        return tool.name

    def _dependency_manifests(self, deps: DependenciesResult) -> list[str]:
        manifests = []
        for group in (deps.python, deps.javascript, deps.go, deps.rust):
            manifests.extend(group.keys())
        return sorted(dict.fromkeys(manifests))

    def _commands(
        self,
        project_intelligence: ProjectIntelligenceResult | None,
        scripts: ScriptsResult | None,
    ) -> list[tuple[str, str]]:
        commands: list[tuple[str, str]] = []
        if scripts:
            for name in ("test", "lint", "build", "typecheck", "dev", "start"):
                if name in scripts.package_json:
                    commands.append((f"npm {name}", f"npm run {name}"))
            for target in scripts.makefile_targets[:5]:
                commands.append((f"make {target}", f"make {target}"))
            for recipe in scripts.justfile_recipes[:5]:
                commands.append((f"just {recipe}", f"just {recipe}"))
            for name in sorted(scripts.pyproject_scripts):
                commands.append((name, name))

        tool_names = {
            tool.name.lower()
            for tools in (project_intelligence.tools.values() if project_intelligence else [])
            for tool in tools
        }
        if "pytest" in tool_names and not self._has_command(commands, "pytest"):
            commands.append(("test", "pytest"))
        if "ruff" in tool_names and not self._has_command(commands, "ruff"):
            commands.append(("lint", "ruff check src/ tests/"))
        if not commands:
            commands.append(("test", "pytest"))
            commands.append(("lint", "ruff check src/ tests/"))
        return commands[:10]

    def _has_command(self, commands: list[tuple[str, str]], needle: str) -> bool:
        return any(needle in command for _label, command in commands)

    def _has_ci(self, cicd: CicdResult) -> bool:
        return bool(
            cicd.github_actions or cicd.gitlab_ci or cicd.circleci or cicd.jenkins_stages
        )

    def _unique_pairs(self, items: list[tuple[str, str]]) -> list[tuple[str, str]]:
        seen = set()
        unique = []
        for path, purpose in items:
            if path in seen:
                continue
            seen.add(path)
            unique.append((path, purpose))
        return unique

    def _is_test_path(self, path: str) -> bool:
        normalized = path.replace("\\", "/").lower()
        name = normalized.split("/")[-1]
        return (
            normalized.startswith("tests/")
            or "/tests/" in normalized
            or normalized.startswith("test/")
            or "/test/" in normalized
            or name.startswith("test_")
            or name.endswith("_test.py")
        )
