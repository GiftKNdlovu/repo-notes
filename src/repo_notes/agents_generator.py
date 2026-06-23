"""AGENTS.md generator — compact repo overview for coding agents."""

from pathlib import Path

from repo_notes.extractors.architecture import ArchitectureResult
from repo_notes.extractors.readme_data import ReadmeData
from repo_notes.extractors.scripts import ScriptsResult
from repo_notes.extractors.stats import StatsResult
from repo_notes.extractors.structure import StructureResult

_FILE_DESCRIPTIONS: dict[str, str] = {
    "README.md": "Project readme",
    "CONTRIBUTING.md": "Contribution guide",
    "LICENSE": "License",
    "pyproject.toml": "Python project configuration",
    "Cargo.toml": "Rust project configuration",
    "go.mod": "Go module definition",
    "package.json": "Node.js project manifest",
    "Dockerfile": "Docker image definition",
    "docker-compose.yml": "Docker Compose configuration",
    "Makefile": "Build automation",
    "justfile": "Build recipes",
    ".env.example": "Environment variable template",
    ".gitignore": "Git ignore rules",
    ".github/": "CI/CD workflows",
}

_DIRECTORY_DESCRIPTIONS: dict[str, str] = {
    "src": "Source code",
    "source": "Source code",
    "lib": "Library code",
    "app": "Application code",
    "cmd": "Command-line entry points",
    "pkg": "Library packages",
    "internal": "Internal packages",
    "api": "API definitions",
    "tests": "Test suite",
    "test": "Test suite",
    "spec": "Test suite",
    "docs": "Documentation",
    "doc": "Documentation",
    "config": "Configuration",
    "cfg": "Configuration",
    "scripts": "Build and utility scripts",
    "bin": "Executables",
    "dist": "Build output",
    "build": "Build artifacts",
    "assets": "Static assets",
    "public": "Static assets",
    "static": "Static assets",
    "migrations": "Database migrations",
    "db": "Database schemas and migrations",
    "docker": "Docker configuration",
    "examples": "Usage examples",
    "benchmarks": "Performance benchmarks",
    "benchmark": "Performance benchmarks",
    "deploy": "Deployment configuration",
    "infra": "Infrastructure as code",
    "proto": "Protobuf definitions",
    "graphql": "GraphQL schema",
    "web": "Web frontend",
    "ui": "UI components",
    "mobile": "Mobile app code",
}


def _format_language_name(language: str) -> str:
    if not language:
        return language
    if any(ch.isupper() for ch in language):
        return language
    return language.title()


def _visible_languages(by_language: dict[str, dict]) -> list[str]:
    languages = sorted(by_language.keys(), key=lambda lang: -by_language[lang]["lines"])
    return [
        _format_language_name(language)
        for language in languages
        if language and language.lower() != "unknown"
    ]


class AgentsGenerator:
    """Generates a compact AGENTS.md focused on agent-oriented repo understanding."""

    def __init__(self, root: Path):
        self.root = root

    def generate(
        self,
        readme_data: ReadmeData | None = None,
        structure: StructureResult | None = None,
        stats: StatsResult | None = None,
        scripts: ScriptsResult | None = None,
        arch: ArchitectureResult | None = None,
    ) -> str:
        sections = [
            self._render_header(readme_data),
            self._render_tech_stack(stats, readme_data),
            self._render_structure(structure),
            self._render_repo_map(structure),
            self._render_architecture(arch),
            self._render_commands(readme_data, scripts),
            self._render_howto(stats, readme_data),
        ]
        return "\n\n".join(s.rstrip() for s in sections if s and s.strip()) + "\n"

    def _render_header(self, data: ReadmeData | None) -> str:
        name = data.name if data and data.name else self.root.name
        desc = data.description if data and data.description else ""
        header = f"# {name}"
        if desc:
            header += f"\n\n{desc}"
        return header

    def _render_tech_stack(self, stats: StatsResult | None, data: ReadmeData | None) -> str:
        lines = ["## Tech Stack", ""]
        has_any = False

        if stats and stats.by_language:
            langs = _visible_languages(stats.by_language)
            if langs:
                lines.append(f"- **Languages**: {', '.join(langs)}")
                has_any = True

        if data:
            if data.python_requires:
                lines.append(f"- **Python**: {data.python_requires}")
                has_any = True
            if data.runtime_deps:
                deps = data.runtime_deps[:12]
                label = ", ".join(deps)
                if len(data.runtime_deps) > 12:
                    label += f" and {len(data.runtime_deps) - 12} more"
                lines.append(f"- **Runtime deps**: {label}")
                has_any = True

        if not has_any:
            return ""

        lines.append("")
        return "\n".join(lines)

    def _render_structure(self, structure: StructureResult | None) -> str:
        if not structure or not structure.tree:
            return ""
        lines = [
            "## Project Structure",
            "",
            "```text",
            structure.tree,
            "```",
            "",
            f"*{structure.file_count} files, {structure.dir_count} directories*",
        ]
        return "\n".join(lines)

    def _render_repo_map(self, structure: StructureResult | None) -> str:
        if not structure or not structure.tree:
            return ""
        children = self._parse_tree_children(structure.tree)
        if not children:
            return ""
        lines = ["## Repository Map", ""]
        for child in sorted(children):
            is_dir = child.endswith("/")
            name = child.rstrip("/")
            if is_dir:
                desc = _DIRECTORY_DESCRIPTIONS.get(name, f"{name}/ directory")
                lines.append(f"- **{name}/** — {desc}")
            else:
                desc = _FILE_DESCRIPTIONS.get(name)
                if desc:
                    lines.append(f"- **{name}** — {desc}")
                else:
                    lines.append(f"- **{name}**")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _parse_tree_children(tree_text: str) -> list[str]:
        children = []
        non_empty_lines = [line for line in tree_text.split("\n") if line.strip()]
        for index, line in enumerate(non_empty_lines):
            # Skip the root line, for example "repo-name/".
            if index == 0:
                continue
            if not line.startswith(" "):
                child = line.strip()
                if child:
                    children.append(child)
        return children

    def _render_architecture(self, arch: ArchitectureResult | None) -> str:
        if not arch:
            return ""
        lines = ["## Architecture", ""]

        if arch.import_graph:
            import_count = sum(len(v) for v in arch.import_graph.values())
            m_label = "module" if len(arch.import_graph) == 1 else "modules"
            v_label = "other module" if import_count == 1 else "other modules"
            v_verb = "imports" if len(arch.import_graph) == 1 else "import"
            lines.append(f"- **{len(arch.import_graph)}** {m_label} {v_verb} **{import_count}** {v_label}")

        if arch.coupling_hotspots:
            top = arch.coupling_hotspots[:3]
            for h in top:
                lines.append(f"- `{h.file}` — {h.total} connections ({h.incoming} in, {h.outgoing} out)")

        if arch.layers:
            layer_labels = ", ".join(sorted(arch.layers.keys()))
            lines.append(f"- **{len(arch.layers)}** layers detected: {layer_labels}")

        if arch.entry_points:
            eps = ", ".join(str(f) for f in arch.entry_points)
            lines.append(f"- Entry points: {eps}")

        if arch.circular_deps:
            lines.append(f"- **{len(arch.circular_deps)}** circular dependenc{'y' if len(arch.circular_deps) == 1 else 'ies'} detected")
            for cycle in arch.circular_deps:
                arrow_chain = " → ".join(cycle)
                lines.append(f"  - `{arrow_chain}`")

        lines.append("")
        return "\n".join(lines)

    def _render_commands(self, data: ReadmeData | None, scripts: ScriptsResult | None) -> str:
        lines = ["## Key Commands", ""]

        if data and data.install_cmd:
            lines.append("```bash")
            lines.append(f"# Install\n{data.install_cmd}")
            lines.append("```")

        if data and data.dev_install_cmd:
            lines.append("```bash")
            lines.append(f"# Dev install\n{data.dev_install_cmd}")
            lines.append("```")

        test_cmds: list[str] = []
        build_cmds: list[str] = []
        if scripts:
            for name, cmd in (scripts.package_json or {}).items():
                lower = name.lower()
                if "test" in lower:
                    test_cmds.append(cmd)
                elif "build" in lower:
                    build_cmds.append(cmd)
            for t in (scripts.makefile_targets or []):
                lower = t.lower()
                if "test" in lower:
                    test_cmds.append(f"make {t}")
                elif "build" in lower:
                    build_cmds.append(f"make {t}")
            for r in (scripts.justfile_recipes or []):
                lower = r.lower()
                if "test" in lower:
                    test_cmds.append(f"just {r}")
                elif "build" in lower:
                    build_cmds.append(f"just {r}")
            for name, cmd in (scripts.pyproject_scripts or {}).items():
                lower = name.lower()
                if "test" in lower:
                    test_cmds.append(cmd)
                elif "build" in lower:
                    build_cmds.append(cmd)

        if test_cmds:
            lines.append("```bash")
            lines.append(f"# Test\n{test_cmds[0]}")
            lines.append("```")

        if build_cmds:
            lines.append("```bash")
            lines.append(f"# Build\n{build_cmds[0]}")
            lines.append("```")
        if not test_cmds:
            lines.append("```bash")
            lines.append("# Test")
            lines.append("pytest")
            lines.append("")
            lines.append("# Lint")
            lines.append("ruff check .")
            lines.append("```")

        lines.append("")
        return "\n".join(lines)

    def _render_howto(self, stats: StatsResult | None, data: ReadmeData | None) -> str:
        lines = ["## How to Work on This Project", ""]

        primaries: list[str] = []
        if stats and stats.by_language:
            primaries = _visible_languages(stats.by_language)[:3]

        if primaries:
            label = ", ".join(primaries)
            version = f" (requires Python {data.python_requires})" if data and data.python_requires else ""
            lines.append(f"This is a **{label}**{version} project.")
        elif data and data.python_requires:
            lines.append(f"This is a Python {data.python_requires} project.")
        else:
            lines.append("This is a project.")
        lines.append("")
        lines.append("Before committing changes, run tests and lint to verify nothing is broken.")
        lines.append("")

        if data and data.install_cmd:
            lines.append("Generate project notes with `repo-notes .`.")
            lines.append("")

        lines.append("_Generated by repo-notes_")

        return "\n".join(lines)
