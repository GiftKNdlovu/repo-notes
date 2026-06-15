"""Extractor for API endpoint detection across frameworks."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from repo_notes.scanner import FileInfo
from repo_notes.file_cache import read_text


FLASK_PATTERN = re.compile(r"""@\w+\.route\(\s*['\"]([^'\"]+)['\"]""")
FASTAPI_PATTERN = re.compile(r"""@\w+\.(?:get|post|put|delete|patch|options|head|trace)\s*\(\s*['\"]([^'\"]+)['\"]""")
DJANGO_PATH_PATTERN = re.compile(r"""path\(\s*['\"]([^'\"]+)['\"]""")
DJANGO_RE_PATH_PATTERN = re.compile(r"""re_path\(\s*['\"]([^'\"]+)['\"]""")
DJANGO_INCLUDE_PATTERN = re.compile(r"""include\(\s*['\"]([^'\"]+)['\"]""")
EXPRESS_PATTERN = re.compile(r"""\w+\.(?:get|post|put|delete|patch|options|head)\s*\(\s*['\"]([^'\"]+)['\"]""")
RAILS_HTTP_PATTERN = re.compile(r"""(?:get|post|put|patch|delete|match)\s+(['\"])([^'\"]+)\1""")
RAILS_RESOURCES_PATTERN = re.compile(r"""resources\s+[:]([a-zA-Z_]\w*)""")


@dataclass(slots=True)
class ApiEndpointResult:
    endpoints: list[dict] = field(default_factory=list)


class ApiEndpointExtractor:
    def extract(self, root: Path, files: list[FileInfo]) -> ApiEndpointResult:
        endpoints: list[dict] = []

        for f in files:
            if f.is_binary:
                continue
            rel = f.relative_path
            rel_str = rel.as_posix()
            content = read_text(f.path)
            if not content:
                continue

            # Flask
            if rel.suffix == ".py":
                for match in FLASK_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    endpoints.append({
                        "framework": "Flask",
                        "method": "any",
                        "path": match.group(1),
                        "file": rel_str,
                        "line": line_num,
                    })

            # FastAPI (non-route decorators like @app.get)
            if rel.suffix == ".py":
                for match in FASTAPI_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    method = match.group(0).split(".")[-1].split("(")[0]
                    endpoints.append({
                        "framework": "FastAPI",
                        "method": method.upper(),
                        "path": match.group(1),
                        "file": rel_str,
                        "line": line_num,
                    })

            # Django — only in urls.py files or files with urlpatterns
            if rel.suffix == ".py" and ("url" in rel_str.lower()):
                for match in DJANGO_PATH_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    endpoints.append({
                        "framework": "Django",
                        "method": "any",
                        "path": match.group(1),
                        "file": rel_str,
                        "line": line_num,
                    })

            # Express.js
            if rel.suffix == ".js" or rel.suffix == ".ts" or rel_suffix_is_mjs(rel.suffix):
                for match in EXPRESS_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    method = match.group(0).split(".")[-1].split("(")[0]
                    endpoints.append({
                        "framework": "Express",
                        "method": method.upper(),
                        "path": match.group(1),
                        "file": rel_str,
                        "line": line_num,
                    })

            # Rails routes.rb
            if rel_str == "config/routes.rb":
                for match in RAILS_HTTP_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    endpoints.append({
                        "framework": "Rails",
                        "method": match.group(0).split()[0].upper(),
                        "path": match.group(2),
                        "file": rel_str,
                        "line": line_num,
                    })
                for match in RAILS_RESOURCES_PATTERN.finditer(content):
                    line_num = content[: match.start()].count("\n") + 1
                    endpoints.append({
                        "framework": "Rails",
                        "method": "RESOURCES",
                        "path": match.group(1),
                        "file": rel_str,
                        "line": line_num,
                    })

        return ApiEndpointResult(endpoints=endpoints)


def rel_suffix_is_mjs(suffix: str) -> bool:
    return suffix == ".mjs"
