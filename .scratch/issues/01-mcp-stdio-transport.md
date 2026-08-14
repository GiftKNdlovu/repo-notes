# 01 — [MCP-1] MCP Stdio Transport & Core Dispatch Engine

GitHub Issue: https://github.com/GiftKNdlovu/repo-notes/issues/2

**What to build:** Launch `repo-notes --mcp` stdio JSON-RPC stdio event loop. Handle standard MCP protocol initialization frames (`initialize`, `ping`, `notifications/initialized`) and tool discovery (`tools/list`).

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] `repo-notes --mcp` launches stdio JSON-RPC server loop reading stdin and writing JSON-RPC 2.0 to stdout.
- [ ] Responds to `initialize` request with MCP server metadata (name, version, capabilities).
- [ ] Responds to `ping` with empty result.
- [ ] Responds to `tools/list` with available tool schemas.
