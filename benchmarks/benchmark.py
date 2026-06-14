"""Benchmark suite for repo-notes.

Measures scan time across synthetic repos of varying sizes.
Usage: python benchmarks/benchmark.py [--runs N] [--quiet]
"""

import argparse
import contextlib
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path


REPO_SIZES = {
    "tiny": {"files": 5, "dirs": 2},
    "small": {"files": 25, "dirs": 5},
    "medium": {"files": 100, "dirs": 10},
    "large": {"files": 500, "dirs": 20},
    "xlarge": {"files": 2000, "dirs": 50},
}


def make_repo(root: Path, num_files: int, num_dirs: int):
    """Generate a synthetic project with realistic file content."""
    dirs = [root]
    for i in range(num_dirs):
        d = root / f"dir_{i:03d}"
        d.mkdir()
        dirs.append(d)

    # Spread files across dirs
    files_per_dir = max(1, num_files // len(dirs))
    file_idx = 0
    for d in dirs:
        for _ in range(files_per_dir):
            if file_idx >= num_files:
                break
            ext = ".py" if file_idx % 3 == 0 else ".js" if file_idx % 3 == 1 else ".ts"
            content = _make_content(file_idx, ext)
            (d / f"mod_{file_idx:04d}{ext}").write_text(content)
            file_idx += 1

    # Write config files
    (root / "pyproject.toml").write_text(
        "[project]\nname = \"benchmark\"\ndependencies = [\"click\", \"flask\"]\n"
    )
    (root / "tsconfig.json").write_text("{\"compilerOptions\": {\"strict\": true}}\n")

    # Nested src dir with __init__
    src = root / "src" / "app"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text("# package\n")
    (src / "main.py").write_text(textwrap.dedent("""\
        \"\"\"Entry point.\"\"\"
        from . import handler
        def main():
            return handler.run()
    """))


def _make_content(idx: int, ext: str) -> str:
    """Generate a small realistic file body."""
    if ext == ".py":
        return textwrap.dedent(f"""\
            \"\"\"Module {idx}.\"\"\"
            import os
            import sys

            CONSTANT = {hash(f"key{idx}") % 1000}

            def func_{idx}():
                return CONSTANT

            class Klass{idx}:
                def method(self):
                    return func_{idx}()
        """)
    elif ext == ".js":
        return textwrap.dedent(f"""\
            // Module {idx}
            const CONSTANT = {hash(f"key{idx}") % 1000};

            function func{idx}() {{
                return CONSTANT;
            }}

            class Klass{idx} {{
                method() {{
                    return func{idx}();
                }}
            }}

            module.exports = {{ func{idx}, Klass{idx} }};
        """)
    else:
        return textwrap.dedent(f"""\
            // Module {idx}
            export const CONSTANT = {hash(f"key{idx}") % 1000};

            export function func{idx}() {{
                return CONSTANT;
            }}

            export class Klass{idx} {{
                method(): number {{
                    return func{idx}();
                }}
            }}
        """)


def run_repo_notes(root: Path, quiet: bool = False) -> float:
    """Run repo-notes and return wall-clock time in seconds."""
    env = os.environ.copy()
    cmd = [sys.executable, "-m", "repo_notes", str(root)]
    if quiet:
        cmd.extend(["--quiet", "--format", "notes"])

    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
    )
    elapsed = time.perf_counter() - start

    if result.returncode != 0:
        print(f"  [ERROR] exit code {result.returncode}: {result.stderr.strip()}", file=sys.stderr)
        return None

    return elapsed


def main():
    parser = argparse.ArgumentParser(description="Benchmark repo-notes scan times")
    parser.add_argument("--runs", type=int, default=3, help="Runs per size (default: 3)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-run output")
    args = parser.parse_args()

    print(f"Benchmarking repo-notes: {args.runs} runs each")
    print(f"{'Size':<8} {'Files':>6} {'Mean (s)':>10} {'Min (s)':>10} {'Max (s)':>10} {'σ (s)':>10}")
    print("-" * 54)

    for label, spec in REPO_SIZES.items():
        times = []
        for run in range(args.runs):
            tmp = tempfile.mkdtemp()
            try:
                make_repo(Path(tmp), spec["files"], spec["dirs"])
                elapsed = run_repo_notes(Path(tmp), quiet=args.quiet)
                if elapsed is not None:
                    times.append(elapsed)
                    if not args.quiet:
                        print(f"  {label} run {run + 1}: {elapsed:.3f}s", file=sys.stderr)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        if times:
            mean = statistics.mean(times)
            sd = statistics.stdev(times) if len(times) > 1 else 0.0
            print(f"{label:<8} {spec['files']:>6} {mean:>10.4f} {min(times):>10.4f} {max(times):>10.4f} {sd:>10.4f}")
        else:
            print(f"{label:<8} {spec['files']:>6} {'FAILED':>10}", file=sys.stderr)


if __name__ == "__main__":
    main()
