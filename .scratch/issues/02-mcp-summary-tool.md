# 02 — [MCP-2] MCP Repo Summary Tool (repo_notes_summary)

GitHub Issue: https://github.com/GiftKNdlovu/repo-notes/issues/3

**What to build:** Enable AI agents to call `repo_notes_summary` tool via MCP stdio JSON-RPC to inspect codebase metrics (total files, lines, total size, language statistics breakdown).

**Blocked by:** 01 — [MCP-1] MCP Stdio Transport & Core Dispatch Engine (https://github.com/GiftKNdlovu/repo-notes/issues/2)

**Status:** ready-for-agent

- [ ] `repo_notes_summary` tool registered in `tools/list`.
- [ ] Executing `tools/call` for `repo_notes_summary` runs file scanner + `StatsExtractor` using `CacheManager`.
- [ ] Returns formatted JSON text content containing file counts, line counts, and language breakdown.
