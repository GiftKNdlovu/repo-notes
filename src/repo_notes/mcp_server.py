"""Model Context Protocol (MCP) server implementation for repo-notes."""

import json
import sys
from pathlib import Path
from typing import Any

from repo_notes import __version__

TOOLS_LIST: list[dict[str, Any]] = [
    {
        "name": "repo_notes_summary",
        "description": "Get repository stats, total lines, file counts, and language breakdown.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "repo_notes_architecture",
        "description": "Get architectural layers, entry points, import graph, and coupling hotspot modules.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "repo_notes_dependencies",
        "description": "Get third-party package dependencies across Python, Node.js, Go, and Rust.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "repo_notes_type_coverage",
        "description": "Get typed vs untyped file metrics and line counts across the repository.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "repo_notes_security_notes",
        "description": "Get high-entropy string findings and potential security notes.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


class MCPServer:
    """MCP Stdio JSON-RPC Server for repo-notes."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    def handle_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        if not isinstance(req, dict):
            return None

        method = req.get("method")
        msg_id = req.get("id")

        # Notifications (no id, no response expected)
        if method == "notifications/initialized":
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "repo-notes-mcp",
                        "version": __version__,
                    },
                },
            }

        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {},
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS_LIST},
            }

        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}",
                },
            }

        return None

    def run_stdio(self) -> None:
        """Run stdio JSON-RPC loop reading stdin and writing stdout."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError:
                err = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": "Parse error"},
                }
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()
