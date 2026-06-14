"""README.md generator."""

from pathlib import Path
from repo_notes.extractors.readme_data import ReadmeData
from repo_notes.extractors.stats import StatsResult


class ReadmeGenerator:
    def __init__(self, root: Path):
        self.root = root

    def generate(
        self,
        readme_data: ReadmeData,
        stats: StatsResult | None = None,
    ) -> str:
        sections = [
            self._render_header(readme_data),
            self._render_badges(readme_data),
            self._render_quick_start(readme_data),
            self._render_features(readme_data),
            self._render_usage(readme_data),
        ]

        if stats:
            sections.append(self._render_stats(stats))

        sections.append(self._render_development(readme_data))
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

    def _render_quick_start(self, data: ReadmeData) -> str:
        lines = ["## Quick Start", ""]
        if data.install_cmd:
            lines.append("```bash")
            lines.append(data.install_cmd)
            lines.append("```")
            lines.append("")
        return "\n".join(lines)

    def _render_features(self, data: ReadmeData) -> str:
        lines = ["## Features", ""]
        if data.runtime_deps:
            lines.append(f"- **{len(data.runtime_deps)} runtime dependencies** — {', '.join(data.runtime_deps[:8])}")
            if len(data.runtime_deps) > 8:
                lines[-1] += f" and {len(data.runtime_deps) - 8} more"
        if data.has_tests:
            lines.append("- **Test suite** — ready for development")
        if data.has_ci:
            lines.append(f"- **CI configured** — {data.ci_provider}")
        if data.has_docker:
            lines.append("- **Docker support** — containerized development")
        lines.append("")
        return "\n".join(lines)

    def _render_usage(self, data: ReadmeData) -> str:
        lines = ["## Usage", ""]
        lines.append("```")
        lines.append(f"{data.name} [OPTIONS] [PATH]")
        lines.append("```")
        lines.append("")
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
        lines.append("")
        return "\n".join(lines)

    def _render_development(self, data: ReadmeData) -> str:
        lines = ["## Development", ""]
        if data.dev_install_cmd:
            lines.append("```bash")
            lines.append(data.dev_install_cmd)
            lines.append("```")
            lines.append("")
        lines.append("### Commands")
        lines.append("")
        lines.append("```bash")
        lines.append("# Run tests")
        lines.append("pytest")
        lines.append("")
        lines.append("# Run linter")
        lines.append("ruff check src/ tests/")
        lines.append("```")
        lines.append("")
        return "\n".join(lines)

    def _render_license(self, data: ReadmeData) -> str:
        if data.license_type:
            return f"## License\n\n{data.license_type}"
        return "## License\n\nMIT"