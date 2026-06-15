"""Directory structure extractor."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from repo_notes.scanner import FileInfo


@dataclass(slots=True)
class StructureResult:
    tree: str
    file_count: int
    dir_count: int


class StructureExtractor:
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth

    def extract(self, root: Path, files: list[FileInfo]) -> StructureResult:
        tree_nodes: dict[str, list[str]] = defaultdict(list)
        all_dirs: set[str] = set()

        for f in files:
            parts = list(f.relative_path.parts)
            if len(parts) > self.max_depth + 1:
                continue
            for i in range(len(parts) - 1):
                parent = "/".join(parts[:i]) if i > 0 else "."
                child = parts[i]
                full = "/".join(parts[: i + 1])
                if child not in tree_nodes[parent]:
                    tree_nodes[parent].append(child)
                all_dirs.add(full)
            # file
            parent = "/".join(parts[:-1]) if len(parts) > 1 else "."
            if parts[-1] not in tree_nodes[parent]:
                tree_nodes[parent].append(parts[-1])

        lines = [root.name + "/"]
        self._render_level(".", tree_nodes, all_dirs, "", lines)

        return StructureResult(
            tree="\n".join(lines),
            file_count=len(files),
            dir_count=len(all_dirs),
        )

    def _render_level(
        self,
        prefix: str,
        tree_nodes: dict[str, list[str]],
        all_dirs: set[str],
        indent: str,
        lines: list[str],
    ):
        children = sorted(tree_nodes.get(prefix, []))
        for child in children:
            full = f"{prefix}/{child}" if prefix != "." else child
            is_dir = child if full in all_dirs else None
            if is_dir:
                entry = f"{child}/"
            else:
                entry = child
            lines.append(f"{indent}{entry}")
            if is_dir and not child.startswith("."):
                self._render_level(full, tree_nodes, all_dirs, indent + "  ", lines)
