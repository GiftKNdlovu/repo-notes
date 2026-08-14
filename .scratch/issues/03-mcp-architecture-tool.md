# 03 — [MCP-3] MCP Architecture & Hotspots Tool (repo_notes_architecture)

GitHub Issue: https://github.com/GiftKNdlovu/repo-notes/issues/4

**What to build:** Enable AI agents to call `repo_notes_architecture` tool via MCP stdio JSON-RPC to discover architectural layers, entry points, import graph, and coupling hotspot modules.

**Blocked by:** 01 — [MCP-1] MCP Stdio Transport & Core Dispatch Engine (https://github.com/GiftKNdlovu/repo-notes/issues/2)

**Status:** ready-for-agent

- [ ] `repo_notes_architecture` tool registered in `tools/list`.
- [ ] Executing `tools/call` for `repo_notes_architecture` runs `ArchitectureExtractor` and returns detected layers, entry points, and coupling hotspots.
- [ ] Incorporates cached results when available.
