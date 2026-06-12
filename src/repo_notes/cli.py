"""CLI interface for repo-notes."""

from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

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
)
from repo_notes.generator import MarkdownGenerator

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
def cli(path, config, output, max_depth, include_hidden):
    """Scan REPO_PATH and generate REPO_NOTES.md with project notes.

    By default, scans the current directory.
    """
    root = path.resolve()
    cfg = Config.load(root=root, path=config)

    # CLI overrides
    overrides = {}
    if max_depth is not None:
        overrides["structure"] = {"max_depth": max_depth}
    if include_hidden is not None:
        overrides["include_hidden"] = include_hidden
    if overrides:
        cfg = cfg.merge_cli(**overrides)

    if output is None:
        output = root / "REPO_NOTES.md"

    console.print(f"[bold]repo-notes[/bold] scanning [cyan]{root}[/cyan]...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        # Scan files
        task = progress.add_task("Scanning files...", total=None)
        files = list(scan_directory(
            root,
            include_hidden=cfg.include_hidden,
            extra_excludes=cfg.exclude_patterns,
        ))
        progress.update(task, completed=True)

        if not files:
            console.print("[yellow]No files found to scan.[/yellow]")
            return

        # Run extractors
        results = {}

        if cfg.extractors.structure:
            task = progress.add_task("Building structure tree...", total=None)
            extractor = StructureExtractor(
                max_depth=cfg.structure.max_depth,
            )
            results["structure"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.key_files:
            task = progress.add_task("Finding key files...", total=None)
            extractor = KeyFilesExtractor()
            results["key_files"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.stats:
            task = progress.add_task("Computing statistics...", total=None)
            extractor = StatsExtractor()
            results["stats"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.dependencies:
            task = progress.add_task("Parsing dependencies...", total=None)
            extractor = DependenciesExtractor()
            results["deps"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.git:
            task = progress.add_task("Gathering git info...", total=None)
            extractor = GitExtractor()
            results["git"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.architecture:
            task = progress.add_task("Analyzing architecture...", total=None)
            extractor = ArchitectureExtractor()
            results["arch"] = extractor.extract(root, files)
            progress.update(task, completed=True)

        if cfg.extractors.security:
            task = progress.add_task("Scanning for secrets...", total=None)
            extractor = SecurityExtractor(
                entropy_threshold=cfg.security.entropy_threshold,
            )
            results["security"] = extractor.extract(root, files)
            progress.update(task, completed=True)

    # Generate markdown
    generator = MarkdownGenerator(root)
    markdown = generator.generate(**results)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")

    console.print(f"[green]Done![/green] Notes written to [bold]{output}[/bold]")
    console.print(f"  - {len(files)} files scanned")
    console.print(f"  - {len(markdown)} characters")