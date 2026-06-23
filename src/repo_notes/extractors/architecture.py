"""Architecture overview extractor."""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from repo_notes.detectors import get_registry
from repo_notes.file_cache import read_text
from repo_notes.scanner import FileInfo

LAYER_PATTERNS = {
    "routes": ["routes", "controllers", "handlers", "endpoints", "api", "views"],
    "services": ["services", "business", "logic", "managers", "usecases", "use_cases"],
    "models": ["models", "entities", "schemas", "dtos", "domain"],
    "repositories": ["repositories", "repository", "dao", "daos", "storage", "persistence"],
    "utils": ["utils", "helpers", "common", "shared", "tools"],
    "config": ["config", "settings", "env"],
    "tests": ["tests", "specs", "__test__", "test_"],
}


@dataclass(slots=True)
class CouplingHotspot:
    file: str
    outgoing: int
    incoming: int
    total: int


@dataclass(slots=True)
class DeadCodeCandidate:
    file: str
    reason: str


@dataclass(slots=True)
class ArchitectureResult:
    layers: dict[str, list[Path]] = field(default_factory=dict)
    import_graph: dict[str, list[str]] = field(default_factory=dict)
    entry_points: list[Path] = field(default_factory=list)
    circular_deps: list[list[str]] = field(default_factory=list)
    coupling_hotspots: list[CouplingHotspot] = field(default_factory=list)
    dead_code_candidates: list[DeadCodeCandidate] = field(default_factory=list)


class ArchitectureExtractor:
    def __init__(self):
        self._registry = get_registry()

    def extract(self, root: Path, files: list[FileInfo]) -> ArchitectureResult:
        layers: dict[str, list[Path]] = defaultdict(list)
        import_graph: dict[str, list[str]] = defaultdict(list)
        entry_points: list[Path] = []

        source_files: set[str] = set()

        for f in files:
            if f.is_binary:
                continue

            lang_info = self._registry.classify(f.path)
            if not lang_info:
                continue

            rel = f.relative_path
            source_files.add(rel.as_posix())
            content = self._read_content(f.path)

            # Detect layer from path
            layer = self._detect_layer(rel)
            if layer:
                layers[layer].append(rel)

            # Detect entry points
            if self._is_entry_point(rel, content, lang_info.name):
                entry_points.append(rel)

            # Extract imports
            imports = self._extract_imports(content, lang_info.name)
            if imports:
                import_graph[rel.as_posix()] = imports

        circular_deps = self._detect_circular_deps(import_graph)

        coupling_hotspots = self._compute_coupling_hotspots(import_graph, source_files)
        dead_code_candidates = self._compute_dead_code_candidates(
            files, import_graph, entry_points, source_files,
        )

        return ArchitectureResult(
            layers=dict(layers),
            import_graph=dict(import_graph),
            entry_points=entry_points,
            circular_deps=circular_deps,
            coupling_hotspots=coupling_hotspots,
            dead_code_candidates=dead_code_candidates,
        )

    def _detect_layer(self, path: Path) -> str | None:
        components = path.as_posix().lower().split("/")
        for layer, patterns in LAYER_PATTERNS.items():
            if any(comp == p or comp.startswith(p.rstrip("*")) for comp in components for p in patterns):
                return layer
        return None

    def _is_entry_point(self, path: Path, content: str, lang: str) -> bool:
        name = path.name.lower()
        entry_names = {
            "python": ["main.py", "app.py", "cli.py", "run.py", "server.py", "manage.py", "__main__.py"],
            "javascript": ["index.js", "main.js", "app.js", "server.js", "cli.js"],
            "typescript": ["index.ts", "main.ts", "app.ts", "server.ts", "cli.ts"],
            "go": ["main.go"],
            "rust": ["main.rs"],
        }
        if name in entry_names.get(lang, []):
            return True

        # Check for common entry patterns in content
        if lang == "python" and ("if __name__ == \"__main__\"" in content):
            return True
        return False

    def _extract_imports(self, content: str, lang: str) -> list[str]:
        imports = []
        if lang == "python":
            for match in re.finditer(r"^\s*(?:from\s+(\S+)\s+)?import\s+(.+)$", content, re.MULTILINE):
                module = match.group(1) or ""
                imports.append(module.strip() if module else match.group(2).split(",")[0].strip())
        elif lang in ("javascript", "typescript"):
            for match in re.finditer(r"^\s*import\s+.*?\s+from\s+['\"](.+?)['\"]", content, re.MULTILINE):
                imports.append(match.group(1))
            for match in re.finditer(r"^\s*const\s+.*?\s*=\s*require\(['\"](.+?)['\"]\)", content, re.MULTILINE):
                imports.append(match.group(1))
        elif lang == "go":
            for match in re.finditer(r"^\s*import\s+\((.*?)\)", content, re.MULTILINE | re.DOTALL):
                for line in match.group(1).split("\n"):
                    line = line.strip().strip('"')
                    if line:
                        imports.append(line)
            for match in re.finditer(r"^\s*import\s+[\"'](.+?)[\"']", content, re.MULTILINE):
                imports.append(match.group(1))
        elif lang == "rust":
            for match in re.finditer(r"^\s*use\s+([^;]+);", content, re.MULTILINE):
                imports.append(match.group(1).split("::")[0])
        return imports

    @staticmethod
    def _compute_coupling_hotspots(
        import_graph: dict[str, list[str]],
        known_files: set[str],
    ) -> list[CouplingHotspot]:
        outgoing: dict[str, int] = {}
        incoming: dict[str, int] = {}
        all_modules: set[str] = set()

        for src, targets in import_graph.items():
            local_targets = []
            for t in targets:
                resolved = ArchitectureExtractor._resolve_target(t, known_files)
                if resolved:
                    local_targets.append(resolved)
            outgoing[src] = len(local_targets)
            all_modules.add(src)
            for resolved in local_targets:
                incoming[resolved] = incoming.get(resolved, 0) + 1
                all_modules.add(resolved)

        hotspots = []
        for mod in sorted(all_modules):
            out_c = outgoing.get(mod, 0)
            in_c = incoming.get(mod, 0)
            total = out_c + in_c
            if total == 0:
                continue
            hotspots.append(CouplingHotspot(
                file=mod,
                outgoing=out_c,
                incoming=in_c,
                total=total,
            ))

        hotspots.sort(key=lambda h: (-h.total, -h.outgoing, h.file))
        return hotspots[:10]

    @staticmethod
    def _is_excluded_from_dead_code(rel: str) -> bool:
        """Check if a file should be excluded from dead-code candidate reporting."""
        name = Path(rel).name
        parts = rel.replace("\\", "/").split("/")
        # Package init files
        if name == "__init__.py":
            return True
        # Test files and directories
        if name.startswith("test_") or name.endswith("_test.py"):
            return True
        if any(p in ("tests", "specs", "__test__") for p in parts):
            return True
        # CLI / entry-point filenames
        if name in ("cli.py", "__main__.py", "main.py", "app.py", "manage.py", "run.py", "server.py", "setup.py"):
            return True
        # Config and build files
        if name in ("setup.cfg", "setup.py", "pyproject.toml", "Makefile", "Dockerfile", "docker-compose.yml", ".env.example"):
            return True
        # Generated / doc artifacts
        if name in ("README.md", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE", "AGENTS.md", "REPO_NOTES.md"):
            return True
        # Directories known to be non-production
        if any(p in ("scripts", "benchmarks", "migrations", "alembic", "docs", "config") for p in parts):
            return True
        return False

    @staticmethod
    def _resolve_target(target: str, known_files: set[str]) -> str | None:
        """Resolve an import target string to a known project file path."""
        if target in known_files:
            return target
        if target + ".py" in known_files:
            return target + ".py"
        name = target.split(".")[-1]
        if name + ".py" in known_files:
            return name + ".py"
        stem = target.replace(".", "/")
        for kf in known_files:
            if kf == stem or kf == stem + ".py":
                return kf
            if kf.endswith("/" + stem) or kf.endswith("/" + stem + ".py"):
                return kf
        return None

    @staticmethod
    def _compute_dead_code_candidates(
        files: list[FileInfo],
        import_graph: dict[str, list[str]],
        entry_points: list[Path],
        known_files: set[str],
    ) -> list[DeadCodeCandidate]:
        entry_paths = {p.as_posix() for p in entry_points}

        incoming: dict[str, int] = {}
        for src, targets in import_graph.items():
            for t in targets:
                resolved = ArchitectureExtractor._resolve_target(t, known_files)
                if resolved:
                    incoming[resolved] = incoming.get(resolved, 0) + 1

        candidates: list[DeadCodeCandidate] = []
        for f in files:
            if f.is_binary:
                continue
            rel = f.relative_path.as_posix()
            if rel not in known_files:
                continue
            if incoming.get(rel, 0) > 0:
                continue
            if rel in entry_paths:
                continue
            if ArchitectureExtractor._is_excluded_from_dead_code(rel):
                continue

            outbound = len(import_graph.get(rel, []))
            if outbound == 0:
                reason = "no inbound local imports; no outbound local imports"
            else:
                reason = f"no inbound local imports; {outbound} outbound local import{'s' if outbound != 1 else ''}"
            candidates.append(DeadCodeCandidate(file=rel, reason=reason))

        candidates.sort(key=lambda c: c.file)
        return candidates[:10]

    @staticmethod
    def _detect_circular_deps(import_graph: dict[str, list[str]]) -> list[list[str]]:
        nodes = set(import_graph.keys())
        adj: dict[str, list[str]] = {n: [] for n in nodes}
        for src, targets in import_graph.items():
            for t in targets:
                if t in nodes or t + ".py" in nodes:
                    match = t if t in nodes else t + ".py"
                    adj[src].append(match)

        unvisited, in_progress, done = 0, 1, 2
        state: dict[str, int] = {n: unvisited for n in nodes}
        cycles: list[list[str]] = []

        def dfs(node: str, stack: list[str]) -> None:
            state[node] = in_progress
            stack.append(node)
            for neighbor in adj.get(node, []):
                nb_state = state.get(neighbor, unvisited)
                if nb_state == in_progress:
                    idx = stack.index(neighbor)
                    cycle = list(stack[idx:])
                    cycle.append(neighbor)
                    cycles.append(cycle)
                elif nb_state == unvisited:
                    dfs(neighbor, stack)
            stack.pop()
            state[node] = done

        for n in sorted(nodes):
            if state[n] == unvisited:
                dfs(n, [])

        return cycles

    def _read_content(self, path: Path) -> str:
        return read_text(path)
