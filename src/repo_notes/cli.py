"""CLI interface for repo-notes."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from repo_notes.cache import CacheManager
from repo_notes.config import Config
from repo_notes.scanner import scan_directory
from repo_notes.extractors import (
    StructureExtractor,
    KeyFilesExtractor,
    StatsExtractor,
    DependenciesExtractor,
    GitExtractor,
    ArchitectureExtractor,
    SecurityExtractor,
    ReadmeDataExtractor,
)
from repo_notes.generator import MarkdownGenerator
from repo_notes.readme_generator import ReadmeGenerator
from repo_notes.html_generator import HtmlGenerator

console = Console()


@click.command()
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
    type=click.Choice(["notes", "readme", "both", "html"]),
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
    "--replace-readme",
    is_flag=True,
    default=False,
    help="Write to README.md instead of rnREADME.md",
)
def cli(path, config, output, max_depth, include_hidden, format, force, quiet, no_cache, replace_readme):
    """Scan REPO_PATH and generate project notes.

    By default, generates REPO_NOTES.md with detailed technical notes.
    Use --format readme to generate a rnREADME.md instead (safe for existing READMEs).
    Use --format readme --replace-readme to write to README.md directly.
    """
    root = path.resolve()
    cfg = Config.load(root=root, path=config)

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
    if not no_cache and cache.is_valid():
        current_states = cache.compute_current_states()
        if not cache.has_changes(current_states):
            console.print("[green]No changes since last scan. Use --no-cache to force re-scan.[/green]")
            return

    console.print(f"[bold]repo-notes[/bold] scanning [cyan]{root}[/cyan]...")

    notes_output = output or root / "REPO_NOTES.md"
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
        if cfg.extractors.key_files:
            extractors.append(("key_files", KeyFilesExtractor(), files))
        if cfg.extractors.stats:
            extractors.append(("stats", StatsExtractor(), files))
        if cfg.extractors.dependencies:
            extractors.append(("deps", DependenciesExtractor(), files))
        if cfg.extractors.git:
            extractors.append(("git", GitExtractor(), files))
        if cfg.extractors.architecture:
            extractors.append(("arch", ArchitectureExtractor(), files))
        if cfg.extractors.security:
            extractors.append(("security", SecurityExtractor(entropy_threshold=cfg.security.entropy_threshold), files))
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

    if cfg.output.format in ("readme", "both"):
        readme_gen = ReadmeGenerator(root)
        readme_md = readme_gen.generate(
            readme_data=readme_data,
            stats=results.get("stats"),
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

    # Update cache after successful scan
    cache.save_from_file_infos(files)