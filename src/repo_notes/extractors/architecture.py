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
class ArchitectureResult:
    layers: dict[str, list[Path]] = field(default_factory=dict)
    import_graph: dict[str, list[str]] = field(default_factory=dict)
    entry_points: list[Path] = field(default_factory=list)
    circular_deps: list[list[str]] = field(default_factory=list)


class ArchitectureExtractor:
    def __init__(self):
        self._registry = get_registry()

    def extract(self, root: Path, files: list[FileInfo]) -> ArchitectureResult:
        layers: dict[str, list[Path]] = defaultdict(list)
        import_graph: dict[str, list[str]] = defaultdict(list)
        entry_points: list[Path] = []

        for f in files:
            if f.is_binary:
                continue

            lang_info = self._registry.classify(f.path)
            if not lang_info:
                continue

            rel = f.relative_path
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

        return ArchitectureResult(
            layers=dict(layers),
            import_graph=dict(import_graph),
            entry_points=entry_points,
            circular_deps=circular_deps,
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
