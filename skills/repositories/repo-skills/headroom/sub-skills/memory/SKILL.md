---
name: memory
description: "Use Headroom persistent memory APIs, memory CLI, MCP/CCR
  retrieval, learning, verbosity, and Codex recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Headroom memory sub-skill

Use this sub-skill when the task is about persistent memory, memory storage maintenance, MCP tools, CCR retrieval, learning from agent transcripts, output verbosity learning, or recovery of Codex state left by Headroom wrappers.

## Route here for

- Python memory APIs: `headroom.memory.Memory`, `with_memory`, `with_memory_tools`, `MemoryConfig`, `HierarchicalMemory`, `LocalBackend`, and local/service-backed memory choices.
- `headroom memory ...` database inspection and maintenance: list, show, stats, edit, repair supersession, delete, prune, purge, export, and import.
- `headroom mcp ...` server install, uninstall, status, and serve workflows, including MCP registry behavior across supported coding agents.
- CCR retrieve behavior: `headroom_retrieve`, `headroom_compress`, `headroom_stats`, proxy-backed retrieval, expired hashes, and MCP tool namespace display.
- `headroom learn` failure learning and `headroom learn --verbosity` output-shaping calibration.
- `headroom recover codex` when Codex sessions/config were left in temporary Headroom homes.

## Route elsewhere

- Proxy base URL setup, provider routing, `headroom proxy`, `headroom wrap`, and `headroom unwrap`: use `proxy-wrap` except for the `--proxy-url` value passed into `headroom mcp install` or `headroom mcp serve`.
- Generic installation, update, deployment lifecycle, `doctor`, savings dashboards, and broad operator diagnostics: use `ops`.
- Non-memory SDK compression APIs, TypeScript SDK basics, image/relevance/spreadsheet helpers, and general `HeadroomClient` usage: use `sdk`.

## Fast start

1. Pick the surface:
   - Local app memory API: read [API reference](references/api-reference.md).
   - Memory database maintenance or MCP registration: read [CLI and MCP reference](references/cli-and-mcp-reference.md).
   - End-to-end recipes: read [workflows](references/workflows.md).
   - Failures: read [troubleshooting](references/troubleshooting.md).
2. Keep memory state scoped. Prefer an explicit temp or app-owned `db_path` for experiments; do not write to arbitrary project roots unless the user chose that location.
3. For any destructive CLI operation, preview first where supported (`--dry-run`, omit `--apply`, or omit `--yes`) and confirm the target database/home.
4. For MCP + CCR issues, distinguish the MCP process from the proxy. The MCP server can compress locally, but proxy-backed retrieval needs a reachable proxy URL.

## Bundled helper

- `scripts/memory_smoke.py` runs a no-credential local memory save/search/delete smoke. It uses a temporary SQLite database by default and accepts `--db-path` for a caller-chosen database and `--json` for machine-readable output.
