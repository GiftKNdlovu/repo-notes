"""HTML generator for repo-notes."""

from io import StringIO
from pathlib import Path
from repo_notes.html_templates import HTML_OPENING, HTML_CLOSING, SIDEBAR_ITEM, BADGES_HTML, SECTION_WRAPPER, CSS, JS
from repo_notes.extractors import (
    StructureResult,
    KeyFilesResult,
    StatsResult,
    DependenciesResult,
    GitResult,
    ArchitectureResult,
    SecurityResult,
)

SECTION_NAMES: dict[str, tuple[str, str]] = {
    "structure": ("📁", "Project Structure"),
    "key_files": ("📄", "Key Files"),
    "stats": ("📊", "Code Statistics"),
    "deps": ("📦", "Dependencies"),
    "git": ("🌿", "Git Information"),
    "arch": ("🏗️", "Architecture Overview"),
    "security": ("🔒", "Security Notes"),
}


class HtmlGenerator:
    def __init__(self, root: Path):
        self.root = root

    def generate(
        self,
        structure: StructureResult | None = None,
        key_files: KeyFilesResult | None = None,
        stats: StatsResult | None = None,
        deps: DependenciesResult | None = None,
        git: GitResult | None = None,
        arch: ArchitectureResult | None = None,
        security: SecurityResult | None = None,
        section_order: list[str] | None = None,
    ) -> str:
        buf = StringIO()
        self.write_to(buf, section_order=section_order, structure=structure, key_files=key_files, stats=stats, deps=deps, git=git, arch=arch, security=security)
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
            "key_files": results.get("key_files"),
            "stats": results.get("stats"),
            "deps": results.get("deps"),
            "git": results.get("git") if results.get("git") and getattr(results.get("git"), "is_repo", False) else None,
            "arch": results.get("arch"),
            "security": results.get("security"),
        }

        renderers = {
            "structure": self._render_structure,
            "key_files": self._render_key_files,
            "stats": self._render_stats,
            "deps": self._render_dependencies,
            "git": self._render_git,
            "arch": self._render_architecture,
            "security": self._render_security,
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
                parts.append(f'<span class="badge badge-success">0 issues</span>')
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

    def _render_key_files(self, result: KeyFilesResult) -> str:
        parts = []
        for cat, files in result.categories.items():
            if not files:
                continue
            label = cat.replace("_", " ").title()
            items = "".join(f"<li>{self._escape(str(f))}</li>" for f in sorted(files))
            parts.append(f"<details class='collapse'><summary>{label} ({len(files)})</summary><ul class='file-list'>{items}</ul></details>")
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