"""CLI interface for repo-notes."""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from repo_notes import __version__
from repo_notes.agents_generator import AgentsGenerator
from repo_notes.cache import CacheManager
from repo_notes.config import Config
from repo_notes.extractors import (
    ApiEndpointExtractor,
    ArchitectureExtractor,
    CicdExtractor,
    ComplexityExtractor,
    DatabaseExtractor,
    DependenciesExtractor,
    DuplicateExtractor,
    EnvVarsExtractor,
    GitExtractor,
    ProjectIntelligenceExtractor,
    ReadmeDataExtractor,
    ScriptsExtractor,
    SecurityExtractor,
    StatsExtractor,
    StructureExtractor,
    TodosExtractor,
    TypeCoverageExtractor,
)
from repo_notes.generator import MarkdownGenerator
from repo_notes.html_generator import HtmlGenerator
from repo_notes.readme_generator import ReadmeGenerator
from repo_notes.scanner import scan_directory

console = Console()

INIT_TEMPLATE = """# repo-notes configuration
# Uncomment and modify as needed.

# Directories or files to exclude (gitignore-style patterns)
# exclude_patterns:
#   - "*.log"
#   - "build/"

# Include hidden files and directories
# include_hidden: false

# Minimum file size in bytes (files smaller than this are skipped)
# min_file_size: 0

# detectors:
#   enabled: ["all"]  # or ["python", "javascript", ...]

# extractors:
#   structure: true
#   stats: true
#   dependencies: true
#   git: true
#   architecture: true
#   security: true
#   todos: true
#   scripts: true
#   env_vars: true
#   cicd: true
#   database: true
#   type_coverage: true
#   complexity: true
#   duplicates: true
#   api_endpoints: true

# security:
#   entropy_threshold: 4.5
#   patterns: []  # custom regex patterns

# structure:
#   max_depth: 3
#   show_hidden: false

# output:
#   format: notes  # notes, readme, agents, both, html, or json
#   order:
#     - structure
#     - stats
#     - deps
#     - git
#     - arch
#     - security
#     - todos
#     - scripts
#     - env_vars
#     - cicd
#     - database
#     - type_coverage
#     - complexity
#     - duplicates
#     - api_endpoints
"""


def _serialize_json(results: dict) -> dict:
    serialized: dict = {}
    for key, val in results.items():
        if val is None:
            continue
        if hasattr(val, "__dataclass_fields__"):
            d = {}
            for fname in val.__dataclass_fields__:
                fval = getattr(val, fname)
                d[fname] = _json_convert(fval)
            serialized[key] = d
        else:
            serialized[key] = _json_convert(val)
    return serialized


def _json_convert(obj):
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, dict):
        return {k: _json_convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_convert(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_json_convert(v) for v in obj)
    return obj


def _find_git_root(path: Path) -> Path | None:
    full = path.resolve()
    for parent in [full] + list(full.parents):
        if not (parent / ".git").exists():
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(parent), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            continue
        if result.returncode != 0:
            continue
        git_root = Path(result.stdout.strip()).resolve()
        if git_root == parent.resolve():
            return parent
    return None


@click.command()
@click.version_option(__version__)
@click.argument(
    "path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
)
@click.option(
    "--config", "-c",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to config file",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path (default: REPO_NOTES.md)",
)
@click.option(
    "--max-depth",
    type=int,
    default=None,
    help="Max depth for directory tree",
)
@click.option(
    "--include-hidden",
    is_flag=True,
    default=None,
    help="Include hidden files and directories",
)
@click.option(
    "--format",
    type=click.Choice(["notes", "readme", "agents", "both", "html", "json"]),
    default=None,
    help="Output format (default: notes)",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing README.md (only with --replace-readme)",
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    default=False,
    help="Suppress progress output",
)
@click.option(
    "--no-cache",
    is_flag=True,
    default=False,
    help="Bypass incremental cache and force full re-scan",
)
@click.option(
    "--init",
    is_flag=True,
    default=False,
    help="Generate a .repo-notes.yaml template in the project root",
)
@click.option(
    "--replace-readme",
    is_flag=True,
    default=False,
    help="Write to README.md instead of rnREADME.md",
)
def cli(path, config, output, max_depth, include_hidden, format, force, quiet, no_cache, init, replace_readme):
    """Scan REPO_PATH and generate project notes.

    By default, generates REPO_NOTES.md with detailed technical notes.
    Use --format readme to generate a rnREADME.md instead (safe for existing READMEs).
    Use --format agents to generate REPO_NOTES_AGENTS.md for AI coding agents.
    Use --format readme --replace-readme to write to README.md directly.
    """
    root = path.resolve()
    git_root = _find_git_root(root)
    if git_root and git_root != root:
        console.print(f"[dim]Auto-detected git root: {git_root}[/dim]")
        root = git_root
    cfg = Config.load(root=root, path=config)

    # --init: generate config template
    if init:
        cfg_path = root / ".repo-notes.yaml"
        if cfg_path.exists() and not force:
            console.print("[yellow].repo-notes.yaml already exists. Use --force to overwrite.[/yellow]")
            return
        cfg_path.write_text(INIT_TEMPLATE)
        console.print(f"[green]Created[/green] {cfg_path}")
        return

    # CLI overrides
    overrides = {}
    if max_depth is not None:
        overrides["structure"] = {"max_depth": max_depth}
    if include_hidden is not None:
        overrides["include_hidden"] = include_hidden
    if format is not None:
        overrides["output"] = {"format": format}
    if overrides:
        cfg = cfg.merge_cli(**overrides)

    cache = CacheManager(root, cfg)
    cache_hit = False
    if not no_cache and cache.is_valid():
        current_states = cache.compute_current_states()
        if not cache.has_changes(current_states):
            cache_hit = True

    if cache_hit:
        console.print("[green]No changes since last scan. Generating output...[/green]")
    else:
        console.print(f"[bold]repo-notes[/bold] scanning [cyan]{root}[/cyan]...")

    notes_output = output or root / "REPO_NOTES.md"
    agents_output = output if cfg.output.format == "agents" and output else root / "REPO_NOTES_AGENTS.md"
    readme_name = "README.md" if replace_readme else "rnREADME.md"
    readme_output = root / readme_name

    if replace_readme and cfg.output.format in ("readme", "both") and readme_output.exists() and not force:
        console.print("[yellow]README.md already exists. Use --force to overwrite.[/yellow]")
        return

    progress_console = Console(file=open(os.devnull, "w")) if quiet else console

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=progress_console,
    ) as progress:
        # Scan files
        task = progress.add_task("Scanning files...", total=None)
        files = list(scan_directory(
            root,
            include_hidden=cfg.include_hidden,
            extra_excludes=cfg.exclude_patterns,
            min_file_size=cfg.min_file_size,
        ))
        progress.update(task, completed=True)

        if not files:
            console.print("[yellow]No files found to scan.[/yellow]")
            return

        # Run extractors in parallel
        results = {}
        extractors: list[tuple[str, object, object]] = []

        if cfg.extractors.structure:
            extractors.append(("structure", StructureExtractor(max_depth=cfg.structure.max_depth), files))
        if cfg.extractors.project_intelligence:
            extractors.append(("project_intelligence", ProjectIntelligenceExtractor(), files))
        if cfg.extractors.stats:
            extractors.append(("stats", StatsExtractor(), files))
        if cfg.extractors.dependencies:
            extractors.append(("deps", DependenciesExtractor(), files))
        if cfg.extractors.git:
            extractors.append(("git", GitExtractor(), files))
        if cfg.extractors.architecture:
            extractors.append(("arch", ArchitectureExtractor(), files))
        if cfg.extractors.security:
            extractors.append(("security", SecurityExtractor(entropy_threshold=cfg.security.entropy_threshold, patterns=cfg.security.patterns), files))
        if cfg.extractors.todos:
            extractors.append(("todos", TodosExtractor(), files))
        if cfg.extractors.scripts:
            extractors.append(("scripts", ScriptsExtractor(), files))
        if cfg.extractors.env_vars:
            extractors.append(("env_vars", EnvVarsExtractor(), files))
        if cfg.extractors.cicd:
            extractors.append(("cicd", CicdExtractor(), files))
        if cfg.extractors.database:
            extractors.append(("database", DatabaseExtractor(), files))
        if cfg.extractors.type_coverage:
            extractors.append(("type_coverage", TypeCoverageExtractor(), files))
        if cfg.extractors.complexity:
            extractors.append(("complexity", ComplexityExtractor(), files))
        if cfg.extractors.duplicates:
            extractors.append(("duplicates", DuplicateExtractor(), files))
        if cfg.extractors.api_endpoints:
            extractors.append(("api_endpoints", ApiEndpointExtractor(), files))
        # README data always extracted
        extractors.append(("readme", ReadmeDataExtractor(), files))

        task = progress.add_task("Running extractors...", total=None)
        readme_data = None
        errors: list[str] = []
        with ThreadPoolExecutor(max_workers=min(8, (os.cpu_count() or 1) * 2)) as pool:
            futures = {pool.submit(ext.extract, root, fls): name for name, ext, fls in extractors}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    if name == "readme":
                        readme_data = result
                    else:
                        results[name] = result
                except Exception as exc:
                    errors.append(f"{name}: {exc}")
        progress.update(task, completed=True)

        if errors:
            for err in errors:
                console.print(f"[yellow]Warning: extractor failed — {err}[/yellow]")

    # Generate outputs
    if cfg.output.format in ("notes", "both"):
        generator = MarkdownGenerator(root)
        notes_output.parent.mkdir(parents=True, exist_ok=True)
        generator.write_to(notes_output, **results, section_order=cfg.output.order)

        size = notes_output.stat().st_size
        console.print(f"[green]Done![/green] Notes written to [bold]{notes_output}[/bold]")
        console.print(f"  - {len(files)} files scanned")
        console.print(f"  - {size:,} bytes")

    if cfg.output.format in ("agents", "both"):
        agents_gen = AgentsGenerator(root)
        agents_output.parent.mkdir(parents=True, exist_ok=True)
        agents_gen.write_to(agents_output, **results)

        size = agents_output.stat().st_size
        console.print(f"[green]Done![/green] Agent notes written to [bold]{agents_output}[/bold]")
        console.print(f"  - {len(files)} files scanned")
        console.print(f"  - {size:,} bytes")

    if cfg.output.format in ("readme", "both"):
        readme_gen = ReadmeGenerator(root)
        readme_md = readme_gen.generate(
            readme_data=readme_data,
            stats=results.get("stats"),
            project_intelligence=results.get("project_intelligence"),
            scripts=results.get("scripts"),
            arch=results.get("arch"),
            deps=results.get("deps"),
            cicd=results.get("cicd"),
            type_coverage=results.get("type_coverage"),
            complexity=results.get("complexity"),
            api_endpoints=results.get("api_endpoints"),
            database=results.get("database"),
        )

        readme_output.parent.mkdir(parents=True, exist_ok=True)
        readme_output.write_text(readme_md, encoding="utf-8")

        name = "README" if replace_readme else "rnREADME"
        console.print(f"[green]Done![/green] {name} written to [bold]{readme_output}[/bold]")

    if cfg.output.format == "html":
        html_gen = HtmlGenerator(root)
        html_output = output or root / "REPO_NOTES.html"
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_gen.write_to(html_output, **results, section_order=cfg.output.order)

        size = html_output.stat().st_size
        console.print(f"[green]Done![/green] HTML notes written to [bold]{html_output}[/bold]")
        console.print(f"  - {len(files)} files scanned")
        console.print(f"  - {size:,} bytes")

    if cfg.output.format == "json":
        import json as json_mod
        json_output = output or root / "REPO_NOTES.json"
        json_output.parent.mkdir(parents=True, exist_ok=True)
        payload = _serialize_json(results)
        json_output.write_text(json_mod.dumps(payload, indent=2), encoding="utf-8")
        size = json_output.stat().st_size
        console.print(f"[green]Done![/green] JSON notes written to [bold]{json_output}[/bold]")
        console.print(f"  - {len(files)} files scanned")
        console.print(f"  - {size:,} bytes")

    # Update cache after successful scan
    cache.save_from_file_infos(files)
