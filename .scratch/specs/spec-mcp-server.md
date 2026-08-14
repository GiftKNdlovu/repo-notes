# Spec: Model Context Protocol (MCP) Server for repo-notes (repo-notes-mcp)

GitHub Issue: https://github.com/GiftKNdlovu/repo-notes/issues/1
Labels: `ready-for-agent`

## Problem Statement

AI coding agents (such as Antigravity, Claude Desktop, Cursor, and Windsurf) lack real-time structured access to repository architecture, coupling hotspots, dependency trees, and type coverage when operating inside developer codebases. Currently, `repo-notes` generates static files (`REPO_NOTES.md`, `AGENTS.md`) which can become stale as code changes, requiring manual re-generation or full file re-reading by AI agents.

## Solution

Provide an official Model Context Protocol (MCP) server for `repo-notes` (`repo-notes-mcp`) running over stdio JSON-RPC. AI agents can dynamically query structured repository intelligence (architecture layers, coupling hotspots, language stats, dependencies, and type coverage) on demand via standard MCP tools.

## User Stories

1. As an AI coding assistant, I want to call a `repo_notes_summary` tool via MCP stdio JSON-RPC, so that I can inspect the full high-level summary of a codebase on demand.
2. As an AI coding assistant, I want to call a `repo_notes_architecture` tool, so that I can discover detected architectural layers, entry points, and high-coupling hotspot modules before proposing refactorings.
3. As an AI coding assistant, I want to call a `repo_notes_dependencies` tool, so that I can inspect declared third-party dependencies across Python, Node.js, Go, and Rust ecosystems.
4. As an AI coding assistant, I want to call a `repo_notes_type_coverage` tool, so that I can identify untyped modules in a repository before writing new features.
5. As a software developer, I want to configure `repo-notes-mcp` in my AI assistant configuration (e.g. `mcpServers` in `claude_desktop_config.json`), so that my AI agent automatically gains deep repo awareness without manual CLI runs.
6. As a software developer, I want `repo-notes-mcp` to automatically leverage incremental caching, so that queries execute in milliseconds on clean working trees.

## Implementation Decisions

- **Module Architecture**: Create an `MCPServer` transport and handler module that wraps `DetectorRegistry` and extractor execution pipelines.
- **Protocol**: Standard MCP JSON-RPC 2.0 protocol over stdio streams (`sys.stdin` / `sys.stdout`).
- **Tool Registrations**: Expose five core tools (`repo_notes_summary`, `repo_notes_architecture`, `repo_notes_dependencies`, `repo_notes_type_coverage`, `repo_notes_security_notes`).
- **Caching Interaction**: The MCP server instance initializes a persistent `CacheManager` to ensure zero redundant scanning across repeated queries.
- **CLI Entrypoint Integration**: Add a `--mcp` flag to the main `repo-notes` CLI binary (`repo-notes --mcp`) to launch the MCP stdio loop.

## Testing Decisions

- **Good Test Definition**: Tests must exercise the external MCP JSON-RPC stdio seam by sending standard JSON-RPC `initialize`, `tools/list`, and `tools/call` request frames and validating standard JSON-RPC 2.0 responses. Tests should avoid checking internal extractor helper functions.
- **Tested Modules**: `MCPServer` stdio transport and JSON-RPC dispatch engine.
- **Prior Art**: Extends existing `cli.py` and `generator.py` test patterns in `tests/`.

## Out of Scope

- HTTP / WebSocket MCP transports (stdio only for v1).
- Direct mutation or editing of source files via MCP.
- Web UI dashboard server.

## Further Notes

- Compatible with official MCP protocol specification (v1.0.0+).
- Operates zero-config when pointed at a repository root.
