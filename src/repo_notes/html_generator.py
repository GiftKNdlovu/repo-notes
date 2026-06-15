"""HTML generator for repo-notes."""

from io import StringIO
from pathlib import Path

from repo_notes.extractors import (
    ApiEndpointResult,
    ArchitectureResult,
    CicdResult,
    ComplexityResult,
    DatabaseResult,
    DependenciesResult,
    DuplicateResult,
    EnvVarsResult,
    GitResult,
    ProjectIntelligenceResult,
    ScriptsResult,
    SecurityResult,
    StatsResult,
    StructureResult,
    TodosResult,
    TypeCoverageResult,
)
from repo_notes.html_templates import (
    BADGES_HTML,
    CSS,
    HTML_CLOSING,
    HTML_OPENING,
    JS,
    SECTION_WRAPPER,
    SIDEBAR_ITEM,
)

SECTION_NAMES: dict[str, tuple[str, str]] = {
    "structure": ("📁", "Project Structure"),
    "project_intelligence": ("🧠", "Project Intelligence"),
    "stats": ("📊", "Code Statistics"),
    "deps": ("📦", "Dependencies"),
    "git": ("🌿", "Git Information"),
    "arch": ("🏗️", "Architecture Overview"),
    "security": ("🔒", "Security Notes"),
    "todos": ("📝", "TODO / FIXME / HACK"),
    "scripts": ("🔧", "Build Scripts"),
    "env_vars": ("🌐", "Environment Variables"),
    "cicd": ("⚙️", "CI/CD Configuration"),
    "database": ("🗄️", "Database Schema"),
    "type_coverage": ("📋", "Type Coverage"),
    "complexity": ("🔍", "Code Complexity"),
    "duplicates": ("📑", "Duplicate Files"),
    "api_endpoints": ("🌐", "API Endpoints"),
}


class HtmlGenerator:
    def __init__(self, root: Path):
        self.root = root

    def generate(
        self,
        structure: StructureResult | None = None,
        project_intelligence: ProjectIntelligenceResult | None = None,
        stats: StatsResult | None = None,
        deps: DependenciesResult | None = None,
        git: GitResult | None = None,
        arch: ArchitectureResult | None = None,
        security: SecurityResult | None = None,
        section_order: list[str] | None = None,
    ) -> str:
        buf = StringIO()
        self.write_to(buf, section_order=section_order, structure=structure, project_intelligence=project_intelligence, stats=stats, deps=deps, git=git, arch=arch, security=security)
        return buf.getvalue()

    def write_to(self, path_or_buf, **results) -> None:
        """Stream output progressively to a file or file-like object without building the full string in memory."""
        close = isinstance(path_or_buf, (str, Path))
        f = open(path_or_buf, "w", encoding="utf-8") if close else path_or_buf
        try:
            self._stream_write(f, **results)
        finally:
            if close:
                f.close()

    def _stream_write(self, f, **results) -> None:
        results_map = {
            "structure": results.get("structure"),
            "project_intelligence": results.get("project_intelligence"),
            "stats": results.get("stats"),
            "deps": results.get("deps"),
            "git": results.get("git") if results.get("git") and getattr(results.get("git"), "is_repo", False) else None,
            "arch": results.get("arch"),
            "security": results.get("security"),
            "todos": results.get("todos"),
            "scripts": results.get("scripts"),
            "env_vars": results.get("env_vars"),
            "cicd": results.get("cicd"),
            "database": results.get("database"),
            "type_coverage": results.get("type_coverage"),
            "complexity": results.get("complexity"),
            "duplicates": results.get("duplicates"),
            "api_endpoints": results.get("api_endpoints"),
        }

        renderers = {
            "structure": self._render_structure,
            "project_intelligence": self._render_project_intelligence,
            "stats": self._render_stats,
            "deps": self._render_dependencies,
            "git": self._render_git,
            "arch": self._render_architecture,
            "security": self._render_security,
            "todos": self._render_todos,
            "scripts": self._render_scripts,
            "env_vars": self._render_env_vars,
            "cicd": self._render_cicd,
            "database": self._render_database,
            "type_coverage": self._render_type_coverage,
            "complexity": self._render_complexity,
            "duplicates": self._render_duplicates,
            "api_endpoints": self._render_api_endpoints,
        }

        order = results.get("section_order") or list(SECTION_NAMES.keys())

        sidebar_items = ""
        for name in order:
            if name not in renderers:
                continue
            result = results_map.get(name)
            if result is not None:
                icon, title = SECTION_NAMES[name]
                sidebar_items += SIDEBAR_ITEM.format(id=name, icon=icon, label=title)

        badges_html = self._render_badges(
            stats=results_map.get("stats"),
            security=results_map.get("security"),
            git=results_map.get("git"),
        )

        f.write(HTML_OPENING.format(
            title=self.root.name,
            css=CSS,
            sidebar=sidebar_items,
            badges=badges_html,
        ))

        for name in order:
            if name not in renderers:
                continue
            result = results_map.get(name)
            if result is not None:
                icon, title = SECTION_NAMES[name]
                content = renderers[name](result)
                f.write(SECTION_WRAPPER.format(id=name, icon=icon, title=title, content=content))

        f.write(HTML_CLOSING.format(js=JS))

    def _render_badges(
        self,
        stats: StatsResult | None = None,
        security: SecurityResult | None = None,
        git: GitResult | None = None,
    ) -> str:
        parts = []
        if stats:
            parts.append(f'<span class="badge">{stats.total_files} files</span>')
            parts.append(f'<span class="badge">{stats.total_lines:,} lines</span>')
            parts.append(f'<span class="badge">{self._format_size(stats.total_size)}</span>')
            langs = len(stats.by_language)
            if langs:
                parts.append(f'<span class="badge">{langs} languages</span>')
        if security:
            high = len(security.findings)
            mild = len(security.high_entropy_strings)
            if high:
                parts.append(f'<span class="badge badge-danger">{high} high</span>')
            if mild:
                parts.append(f'<span class="badge badge-warning">{mild} mild</span>')
            if not high and not mild:
                parts.append('<span class="badge badge-success">0 issues</span>')
        if git and git.is_repo:
            parts.append(f'<span class="badge badge-success">branch {git.current_branch}</span>')
        return BADGES_HTML.format(badges=" ".join(parts)) if parts else ""

    def _render_structure(self, result: StructureResult) -> str:
        lines = result.tree.strip().split("\n")
        items: list[tuple[int, str, str, bool]] = []
        for line in lines:
            stripped = line.lstrip(" ")
            depth = (len(line) - len(stripped)) // 2
            is_dir = stripped.endswith("/")
            name = stripped.rstrip("/")
            icon = "\U0001f4c1" if is_dir else "\U0001f4c4"
            items.append((depth, icon, name, is_dir))
        html = self._build_tree_html(items)
        return f'{html}<div class="fcount">{result.file_count} files, {result.dir_count} directories</div>'

    def _build_tree_html(self, items: list[tuple[int, str, str, bool]]) -> str:
        if not items:
            return '<div class="tree"><p class="fcount">No files</p></div>'
        parts = [
            '<div class="tree">',
            '<div class="tb"><button class="tbtn" onclick="collapseAll()">&#9660; Collapse All</button>'
            '<button class="tbtn" onclick="expandAll()">&#9650; Expand All</button>'
            '<input class="tsrc" placeholder="Filter..." oninput="filterTree(this)"></div>',
            '<div class="tscroll"><ul>',
        ]
        prev_depth = 0
        for i, (depth, icon, name, is_dir) in enumerate(items):
            label = f'<span class="tn{" td" if is_dir else ""}">{self._escape(name)}</span>'
            if is_dir:
                inner = (
                    f'<div class="th" onclick="toggleTreeFolder(this)">'
                    f'<span class="tt">&#9660;</span>'
                    f'<span class="ti">{icon}</span>{label}</div>'
                )
                li_open = f'<li class="tf">{inner}'
                li_child = "<ul>"
            else:
                li_open = f"<li><span class=\"ti\">{icon}</span>{label}"
                li_child = ""
            if i == 0:
                parts.append(li_open)
                if li_child:
                    parts.append(li_child)
                prev_depth = depth
                continue
            if depth > prev_depth:
                parts.append(li_open)
                if li_child:
                    parts.append(li_child)
                prev_depth = depth
            elif depth == prev_depth:
                if parts[-1] == "<ul>":
                    parts.pop()
                parts.append("</li>")
                parts.append(li_open)
                if li_child:
                    parts.append(li_child)
                prev_depth = depth
            else:
                while prev_depth > depth:
                    if parts[-1] == "<ul>":
                        parts.pop()
                    parts.append("</li></ul>")
                    prev_depth -= 1
                if parts[-1] == "<ul>":
                    parts.pop()
                parts.append("</li>")
                parts.append(li_open)
                if li_child:
                    parts.append(li_child)
                prev_depth = depth
        while prev_depth >= 0:
            if parts[-1] == "<ul>":
                parts.pop()
            parts.append("</li></ul>")
            prev_depth -= 1
        parts.append("</ul></div></div>")
        return "".join(parts)

    def _render_project_intelligence(self, result: ProjectIntelligenceResult) -> str:
        parts = []

        by_cat_order = [
            "Languages", "Frameworks", "Build", "Testing", "Linting",
            "Database", "Messaging", "Containers", "Cloud",
            "Monitoring", "Documentation", "Automation", "Mobile", "Utilities",
        ]

        if result.total_tools:
            badge = f"<p><strong>{result.total_tools}</strong> tools detected across <strong>{result.total_categories}</strong> categories.</p>"
            parts.append(badge)

        for cat in by_cat_order:
            tools = result.tools.get(cat)
            if not tools:
                continue
            rows = "".join(
                f"<tr><td><strong>{self._escape(t.name)}</strong></td><td>{self._escape(t.version) if t.version else '—'}</td><td>{'<code>' + self._escape(t.config_file) + '</code>' if t.config_file else '—'}</td></tr>"
                for t in sorted(tools, key=lambda x: x.name.lower())
            )
            parts.append(
                f"<details class='collapse' open><summary>{cat} ({len(tools)})</summary>"
                f"<div class='table-wrap'><table><thead><tr><th>Tool</th><th>Version</th><th>Config</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></div></details>"
            )

        if result.categories:
            items = ""
            for cat, files in sorted(result.categories.items()):
                label = cat.replace("_", " ").title()
                files_str = ", ".join(f"<code>{self._escape(str(f))}</code>" for f in sorted(files))
                items += f"<li><strong>{label}:</strong> {files_str}</li>"
            parts.append(f"<details class='collapse' open><summary>Key Files ({sum(len(v) for v in result.categories.values())})</summary><ul class='file-list'>{items}</ul></details>")

        return "".join(parts)

    def _render_stats(self, result: StatsResult) -> str:
        parts = [
            '<div class="stats-grid">',
            f'<div class="stat-card"><div class="stat-value">{result.total_files}</div><div class="stat-label">Files</div></div>',
            f'<div class="stat-card"><div class="stat-value">{result.total_lines:,}</div><div class="stat-label">Lines</div></div>',
            f'<div class="stat-card"><div class="stat-value">{self._format_size(result.total_size)}</div><div class="stat-label">Size</div></div>',
            f'<div class="stat-card"><div class="stat-value">{len(result.by_language)}</div><div class="stat-label">Languages</div></div>',
            '</div>',
        ]

        if result.by_language:
            max_lines = max(d["lines"] for d in result.by_language.values()) if result.by_language else 1
            lang_colors = ["#0969da", "#cf222e", "#1a7f37", "#9a6700", "#8250df", "#bf3989", "#0550ae", "#656d76"]
            bars = []
            for i, (lang, data) in enumerate(sorted(result.by_language.items(), key=lambda x: -x[1]["lines"])):
                pct = min(data["lines"] / max_lines * 100, 100) if max_lines else 0
                color = lang_colors[i % len(lang_colors)]
                bars.append(f'<div class="lang-bar"><span style="width:80px;font-size:12px">{self._escape(lang)}</span><div class="bar"><div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div></div><span style="width:60px;text-align:right;font-size:12px;color:var(--text-secondary)">{data["files"]} files</span><span style="width:60px;text-align:right;font-size:12px;color:var(--text-secondary)">{data["lines"]:,} lines</span></div>')
            parts.append("<details class='collapse' open><summary>By Language</summary>" + "".join(bars) + "</details>")

        if result.largest_files:
            rows = "".join(f"<tr><td>{self._escape(str(p))}</td><td style='text-align:right'>{line_count:,}</td></tr>" for p, line_count in result.largest_files)
            parts.append(f"<details class='collapse' open><summary>Largest Files (top {len(result.largest_files)})</summary><div class='table-wrap'><table><thead><tr><th>File</th><th>Lines</th></tr></thead><tbody>{rows}</tbody></table></div></details>")

        return "".join(parts)

    def _render_dependencies(self, result: DependenciesResult) -> str:
        parts = []
        for ecosystem, label in [
            (result.python, "Python"),
            (result.javascript, "JavaScript/TypeScript"),
            (result.go, "Go"),
            (result.rust, "Rust"),
        ]:
            if not ecosystem:
                continue
            rows = ""
            for file, deps in ecosystem.items():
                if isinstance(deps, dict):
                    items = "".join(f"<li><strong>{k}</strong>: {self._describe_dep(v)}</li>" for k, v in deps.items())
                elif isinstance(deps, list):
                    items = "".join(f"<li>{self._escape(d)}</li>" for d in deps)
                else:
                    items = f"<li>{self._escape(str(deps))}</li>"
                rows += f"<details class='collapse'><summary>{self._escape(file)}</summary><ul class='file-list'>{items}</ul></details>"
            parts.append(f"<details class='collapse' open><summary>{label} ({len(ecosystem)} files)</summary>{rows}</details>")
        return "".join(parts)

    def _render_git(self, result: GitResult) -> str:
        parts = [
            '<div class="stats-grid" style="grid-template-columns:repeat(auto-fit,minmax(120px,1fr))">',
            f'<div class="stat-card"><div class="stat-value">{self._escape(result.current_branch)}</div><div class="stat-label">Branch</div></div>',
            f'<div class="stat-card"><div class="stat-value">{len(result.recent_commits)}</div><div class="stat-label">Recent Commits</div></div>',
            f'<div class="stat-card"><div class="stat-value">{len(result.branches)}</div><div class="stat-label">Branches</div></div>',
            f'<div class="stat-card"><div class="stat-value">{len(result.contributors)}</div><div class="stat-label">Contributors</div></div>',
            '</div>',
        ]
        if result.remote_url:
            parts.append(f'<p style="margin-bottom:8px">Remote: <code>{self._escape(result.remote_url)}</code></p>')

        if result.recent_commits:
            commits = "".join(
                f'<li class="commit-item"><div class="commit-msg">{self._escape(c["message"][:80])}</div><div class="commit-meta">{c["hash"]} by {self._escape(c["author"])} on {c["date"]}</div></li>'
                for c in result.recent_commits
            )
            parts.append(f"<details class='collapse' open><summary>Recent Commits ({len(result.recent_commits)})</summary><ul class='commit-list'>{commits}</ul></details>")

        if result.branches:
            branches = "".join(f"<li>{self._escape(b)}</li>" for b in result.branches[:30])
            if len(result.branches) > 30:
                branches += f"<li><em>...and {len(result.branches) - 30} more</em></li>"
            parts.append(f"<details class='collapse' open><summary>Branches ({len(result.branches)})</summary><ul class='file-list'>{branches}</ul></details>")

        if result.contributors:
            rows = "".join(f"<tr><td>{self._escape(c['name'])}</td><td style='text-align:right'>{c['commits']}</td></tr>" for c in result.contributors[:15])
            parts.append(f"<details class='collapse' open><summary>Top Contributors ({len(result.contributors)})</summary><div class='table-wrap'><table><thead><tr><th>Contributor</th><th>Commits</th></tr></thead><tbody>{rows}</tbody></table></div></details>")

        return "".join(parts)

    def _render_architecture(self, result: ArchitectureResult) -> str:
        parts = []
        if result.layers:
            cards = ""
            for layer, files in sorted(result.layers.items()):
                file_items = "".join(f"<li>{self._escape(str(f))}</li>" for f in sorted(files)[:10])
                if len(files) > 10:
                    file_items += f"<li><em>...and {len(files) - 10} more</em></li>"
                cards += f'<div class="layer-card"><h4>{layer.title()}</h4><span class="file-count">{len(files)} files</span><ul class="file-list">{file_items}</ul></div>'
            parts.append(f"<details class='collapse' open><summary>Detected Layers ({len(result.layers)})</summary><div class='layer-grid'>{cards}</div></details>")

        if result.entry_points:
            eps = "".join(f'<span class="entry-point">{self._escape(str(f))}</span>' for f in sorted(result.entry_points))
            parts.append(f"<h4 style='margin-top:12px'>Entry Points</h4><div class='entry-points'>{eps}</div>")

        if result.import_graph:
            rows = "".join(
                f'<tr><td><code>{self._escape(f)}</code></td><td><code>{", ".join(self._escape(i) for i in sorted(imports[:8]))}{", ..." if len(imports) > 8 else ""}</code></td></tr>'
                for f, imports in sorted(result.import_graph.items())
            )
            parts.append(f"<details class='collapse'><summary>Import Graph ({len(result.import_graph)} files)</summary><table><thead><tr><th>File</th><th>Imports</th></tr></thead><tbody>{rows}</tbody></table></details>")

        return "".join(parts)

    def _render_security(self, result: SecurityResult) -> str:
        parts = []
        if result.env_files:
            items = "".join(f"<li>{self._escape(str(f))} &#9888;&#65039;</li>" for f in result.env_files)
            parts.append(f'<div class="alert alert-warning"><strong>Environment Files Found</strong><ul class="file-list">{items}</ul></div>')

        if result.findings:
            rows = "".join(
                f'<tr><td><code>{self._escape(f["file"])}</code></td><td>{f["type"]}</td><td>{f["line"]}</td><td><code>{self._escape(f["preview"])}</code></td></tr>'
                for f in result.findings[:30]
            )
            if len(result.findings) > 30:
                rows += f'<tr><td colspan="4"><em>...and {len(result.findings) - 30} more</em></td></tr>'
            parts.append(f"<details class='collapse' open><summary>Potential Secrets ({len(result.findings)})</summary><div class='table-wrap'><table><thead><tr><th>File</th><th>Type</th><th>Line</th><th>Preview</th></tr></thead><tbody>{rows}</tbody></table></div></details>")

        if result.high_entropy_strings:
            rows = "".join(
                f'<tr><td><code>{self._escape(f["file"])}</code></td><td>{f["entropy"]}</td><td>{f["line"]}</td><td><code>{self._escape(f["preview"])}</code></td></tr>'
                for f in result.high_entropy_strings[:20]
            )
            parts.append(f"<details class='see-more'><summary>High Entropy Strings ({len(result.high_entropy_strings)} found, review recommended)</summary><div class='table-wrap'><table><thead><tr><th>File</th><th>Entropy</th><th>Line</th><th>Preview</th></tr></thead><tbody>{rows}</tbody></table></div></details>")

        return "".join(parts)

    def _render_todos(self, result: TodosResult) -> str:
        if not result.items:
            return "<p>No developer comments found.</p>"
        tag_order = ["FIXME", "HACK", "TODO", "XXX", "BUG", "WORKAROUND", "HACKME"]
        parts = []
        for tag in tag_order:
            tag_items = [i for i in result.items if i["tag"] == tag]
            if not tag_items:
                continue
            total = result.count_by_tag.get(tag, 0)
            rows = "".join(
                f'<tr><td><code>{self._escape(i["file"])}</code></td><td>{i["line"]}</td><td>{self._escape(i["message"])}</td></tr>'
                for i in tag_items
            )
            header = f"{tag} ({total} total)"
            if total > len(tag_items):
                header += f" — top {len(tag_items)}"
            parts.append(
                f"<details class='collapse' open><summary>{header}</summary>"
                f"<div class='table-wrap'><table><thead><tr><th>File</th><th>Line</th><th>Message</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></div></details>"
            )
        return "".join(parts)

    def _render_scripts(self, result: ScriptsResult) -> str:
        parts = []
        if result.package_json:
            items = "".join(
                f"<li><strong>{self._escape(k)}</strong>: <code>{self._escape(v)}</code></li>"
                for k, v in sorted(result.package_json.items())
            )
            parts.append(f"<details class='collapse' open><summary>package.json Scripts ({len(result.package_json)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.makefile_targets:
            items = "".join(f"<li><code>{self._escape(t)}</code></li>" for t in result.makefile_targets[:30])
            if len(result.makefile_targets) > 30:
                items += f"<li><em>...and {len(result.makefile_targets) - 30} more</em></li>"
            parts.append(f"<details class='collapse' open><summary>Makefile Targets ({len(result.makefile_targets)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.justfile_recipes:
            items = "".join(f"<li><code>{self._escape(r)}</code></li>" for r in result.justfile_recipes[:30])
            if len(result.justfile_recipes) > 30:
                items += f"<li><em>...and {len(result.justfile_recipes) - 30} more</em></li>"
            parts.append(f"<details class='collapse' open><summary>Justfile Recipes ({len(result.justfile_recipes)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.pyproject_scripts:
            items = "".join(
                f"<li><strong>{self._escape(k)}</strong>: <code>{self._escape(v)}</code></li>"
                for k, v in sorted(result.pyproject_scripts.items())
            )
            parts.append(f"<details class='collapse' open><summary>pyproject.toml Scripts ({len(result.pyproject_scripts)})</summary><ul class='file-list'>{items}</ul></details>")
        if not parts:
            return "<p>No build scripts found.</p>"
        return "".join(parts)

    def _render_env_vars(self, result: EnvVarsResult) -> str:
        if not result.variables:
            return "<p>No environment variable references found.</p>"
        rows = "".join(
            f'<tr><td><code>{self._escape(var)}</code></td><td>{", ".join(f"<code>{f}</code>" for f in files[:5])}{" <em>..." if len(files) > 5 else ""}</td></tr>'
            for var, files in list(result.variables.items())[:40]
        )
        return (
            f"<p><strong>{len(result.variables)}</strong> unique environment variables referenced.</p>"
            f"<div class='table-wrap'><table><thead><tr><th>Variable</th><th>Files</th></tr></thead>"
            f"<tbody>{rows}</tbody></table></div>"
        )

    def _render_cicd(self, result: CicdResult) -> str:
        parts = []
        if result.github_actions:
            items = ""
            for wf in result.github_actions:
                on = ", ".join(wf["on"]) if isinstance(wf["on"], list) else str(wf["on"])
                jobs = ", ".join(wf["jobs"][:8])
                if len(wf["jobs"]) > 8:
                    jobs += ", ..."
                items += f"<li><strong>{self._escape(wf['name'])}</strong> — on {on}<br><small>Jobs: {jobs}</small></li>"
            parts.append(f"<details class='collapse' open><summary>GitHub Actions ({len(result.github_actions)} workflows)</summary><ul class='file-list'>{items}</ul></details>")
        if result.gitlab_ci:
            stages = sorted(set(j["stage"] for j in result.gitlab_ci))
            items = "".join(
                f"<li><strong>{self._escape(j['name'])}</strong> (stage: {j['stage']}){(' <code>' + self._escape(j['image']) + '</code>') if j['image'] else ''}</li>"
                for j in result.gitlab_ci
            )
            parts.append(f"<details class='collapse' open><summary>GitLab CI — Stages: {', '.join(stages)} ({len(result.gitlab_ci)} jobs)</summary><ul class='file-list'>{items}</ul></details>")
        if result.circleci:
            items = "".join(f"<li><strong>{self._escape(j['name'])}</strong> — {j['steps']} steps</li>" for j in result.circleci)
            parts.append(f"<details class='collapse' open><summary>CircleCI ({len(result.circleci)} jobs)</summary><ul class='file-list'>{items}</ul></details>")
        if result.jenkins_stages:
            items = "".join(f"<li>{self._escape(s)}</li>" for s in result.jenkins_stages)
            parts.append(f"<details class='collapse' open><summary>Jenkins Pipeline ({len(result.jenkins_stages)} stages)</summary><ul class='file-list'>{items}</ul></details>")
        if not parts:
            return "<p>No CI/CD configuration found.</p>"
        return "".join(parts)

    def _render_database(self, result: DatabaseResult) -> str:
        parts = []
        if result.orm_types:
            items = "".join(f"<li>{self._escape(t)}</li>" for t in result.orm_types)
            parts.append(f"<details class='collapse' open><summary>Detected ORM ({len(result.orm_types)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.model_count:
            parts.append(f"<p><strong>{result.model_count}</strong> models across {len(result.model_files)} files</p>")
        if result.migration_files:
            items = "".join(f"<li><code>{self._escape(str(m))}</code></li>" for m in result.migration_files[:15])
            if len(result.migration_files) > 15:
                items += f"<li><em>...and {len(result.migration_files) - 15} more</em></li>"
            parts.append(f"<details class='collapse' open><summary>Migration Files ({len(result.migration_files)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.schema_files:
            items = "".join(f"<li><code>{self._escape(str(s))}</code></li>" for s in result.schema_files)
            parts.append(f"<details class='collapse' open><summary>Schema Files ({len(result.schema_files)})</summary><ul class='file-list'>{items}</ul></details>")
        if result.model_files:
            items = "".join(f"<li><code>{self._escape(str(m))}</code></li>" for m in result.model_files[:15])
            if len(result.model_files) > 15:
                items += f"<li><em>...and {len(result.model_files) - 15} more</em></li>"
            parts.append(f"<details class='collapse' open><summary>Model Files ({len(result.model_files)})</summary><ul class='file-list'>{items}</ul></details>")
        if not parts:
            return "<p>No database schema detected.</p>"
        return "".join(parts)

    def _render_type_coverage(self, result: TypeCoverageResult) -> str:
        total = result.typed_files + result.untyped_files
        if total == 0:
            return "<p>No typed or untyped files found.</p>"
        pct = round(result.typed_files / total * 100, 1) if total else 0
        html = f"""
<div class='stats-grid' style='grid-template-columns:repeat(auto-fit,minmax(140px,1fr))'>
  <div class='stat-card'><div class='stat-value'>{pct}%</div><div class='stat-label'>Typed</div></div>
  <div class='stat-card'><div class='stat-value'>{result.typed_files}</div><div class='stat-label'>Typed Files</div></div>
  <div class='stat-card'><div class='stat-value'>{result.untyped_files}</div><div class='stat-label'>Untyped Files</div></div>
  <div class='stat-card'><div class='stat-value'>{result.typed_lines:,}</div><div class='stat-label'>Typed Lines</div></div>
</div>"""
        if result.by_extension:
            rows = "".join(
                f"<tr><td>{ext}</td><td style='text-align:right'>{d['files']}</td><td style='text-align:right'>{d['typed_lines']:,}</td><td style='text-align:right'>{d['untyped_lines']:,}</td></tr>"
                for ext, d in sorted(result.by_extension.items())
            )
            html += f"<details class='collapse' open><summary>By Extension ({len(result.by_extension)})</summary><div class='table-wrap'><table><thead><tr><th>Extension</th><th>Files</th><th>Typed Lines</th><th>Untyped Lines</th></tr></thead><tbody>{rows}</tbody></table></div></details>"
        return html

    def _render_complexity(self, result: ComplexityResult) -> str:
        html = f"""
<div class='stats-grid' style='grid-template-columns:repeat(auto-fit,minmax(180px,1fr))'>
  <div class='stat-card'><div class='stat-value'>{result.avg_function_length}</div><div class='stat-label'>Avg Function Lines</div></div>
  <div class='stat-card'><div class='stat-value'>{result.max_nesting}</div><div class='stat-label'>Max Nesting</div></div>
</div>"""
        if result.complex_files:
            rows = "".join(
                f"<tr><td><code>{self._escape(e['file'])}</code></td><td style='text-align:right'>{len(e['long_functions'])}</td><td style='text-align:right'>{e['max_nesting']}</td><td style='text-align:right'>{e['score']}</td></tr>"
                for e in result.complex_files
            )
            html += f"<details class='collapse' open><summary>Complex Files ({len(result.complex_files)})</summary><div class='table-wrap'><table><thead><tr><th>File</th><th>Long Functions</th><th>Max Nesting</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table></div></details>"
        else:
            html += "<p>No complex files detected.</p>"
        return html

    def _render_duplicates(self, result: DuplicateResult) -> str:
        if result.total_duplicates == 0:
            return "<p>No duplicate files found.</p>"
        html = f"<p><strong>{result.total_duplicates}</strong> duplicate file(s) found"
        if result.total_saved_bytes:
            html += f", <strong>{self._format_size(result.total_saved_bytes)}</strong> could be saved"
        html += "</p>"
        if result.duplicates:
            rows = "".join(
                f"<tr><td><code>{self._escape(d['file'])}</code></td><td><code>{self._escape(d['duplicate_of'])}</code></td><td>{self._format_size(d['size'])}</td><td>{d['similarity']*100:.0f}%</td></tr>"
                for d in result.duplicates[:20]
            )
            html += f"<div class='table-wrap'><table><thead><tr><th>Duplicate File</th><th>Original</th><th>Size</th><th>Similarity</th></tr></thead><tbody>{rows}</tbody></table></div>"
        return html

    def _render_api_endpoints(self, result: ApiEndpointResult) -> str:
        if not result.endpoints:
            return "<p>No API endpoints detected.</p>"
        by_framework: dict[str, list[dict]] = {}
        for ep in result.endpoints:
            by_framework.setdefault(ep["framework"], []).append(ep)
        parts = []
        for framework in ["FastAPI", "Flask", "Django", "Express", "Rails"]:
            fw_eps = by_framework.get(framework)
            if not fw_eps:
                continue
            rows = "".join(
                f"<tr><td>{ep['method']}</td><td><code>{self._escape(ep['path'])}</code></td><td><code>{self._escape(ep['file'])}</code></td><td>{ep['line']}</td></tr>"
                for ep in sorted(fw_eps, key=lambda x: (x["path"], x["method"]))
            )
            parts.append(
                f"<details class='collapse' open><summary>{framework} ({len(fw_eps)} endpoints)</summary>"
                f"<div class='table-wrap'><table><thead><tr><th>Method</th><th>Path</th><th>File</th><th>Line</th></tr></thead>"
                f"<tbody>{rows}</tbody></table></div></details>"
            )
        return "".join(parts)

    def _describe_dep(self, val) -> str:
        if isinstance(val, dict):
            return f"{len(val)} packages"
        if isinstance(val, list):
            return f"{len(val)} entries"
        return str(val)

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _escape(self, s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
