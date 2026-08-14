# 05 — [MCP-5] End-to-End MCP Stdio Integration Test Suite

GitHub Issue: https://github.com/GiftKNdlovu/repo-notes/issues/6

**What to build:** Create automated test suite in `tests/test_mcp_server.py` exercising stdio JSON-RPC request and response frames end-to-end against real test repositories.

**Blocked by:**
- 02 — [MCP-2] MCP Repo Summary Tool (https://github.com/GiftKNdlovu/repo-notes/issues/3)
- 03 — [MCP-3] MCP Architecture & Hotspots Tool (https://github.com/GiftKNdlovu/repo-notes/issues/4)
- 04 — [MCP-4] MCP Dependencies & Type Coverage Tools (https://github.com/GiftKNdlovu/repo-notes/issues/5)

**Status:** ready-for-agent

- [ ] Automated tests send `initialize`, `ping`, `tools/list`, and `tools/call` JSON-RPC frames over stdio.
- [ ] Validates exact JSON-RPC 2.0 response schema and return payloads.
- [ ] Included in `pytest` test suite execution.
