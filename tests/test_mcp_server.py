"""Tests for Model Context Protocol (MCP) server implementation."""

import json
from pathlib import Path

from repo_notes.mcp_server import MCPServer


def test_mcp_initialize(tmp_path: Path):
    server = MCPServer(tmp_path)
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"},
        },
    }
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "result" in resp
    res = resp["result"]
    assert res["protocolVersion"] == "2024-11-05"
    assert res["serverInfo"]["name"] == "repo-notes-mcp"
    assert "tools" in res["capabilities"]


def test_mcp_ping(tmp_path: Path):
    server = MCPServer(tmp_path)
    req = {"jsonrpc": "2.0", "id": 2, "method": "ping"}
    resp = server.handle_request(req)
    assert resp == {"jsonrpc": "2.0", "id": 2, "result": {}}


def test_mcp_tools_list(tmp_path: Path):
    server = MCPServer(tmp_path)
    req = {"jsonrpc": "2.0", "id": 3, "method": "tools/list"}
    resp = server.handle_request(req)
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 3
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "repo_notes_summary" in tool_names
    assert "repo_notes_architecture" in tool_names
    assert "repo_notes_dependencies" in tool_names
    assert "repo_notes_type_coverage" in tool_names
    assert "repo_notes_security_notes" in tool_names


def test_mcp_initialized_notification(tmp_path: Path):
    server = MCPServer(tmp_path)
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    resp = server.handle_request(notif)
    assert resp is None


def test_mcp_cli_flag(tmp_path: Path):
    from click.testing import CliRunner

    from repo_notes.cli import cli

    runner = CliRunner()
    input_str = json.dumps({"jsonrpc": "2.0", "id": 99, "method": "ping"}) + "\n"
    result = runner.invoke(cli, [str(tmp_path), "--mcp"], input=input_str)
    assert result.exit_code == 0
    resp = json.loads(result.output.strip())
    assert resp == {"jsonrpc": "2.0", "id": 99, "result": {}}

