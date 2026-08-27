# Memory troubleshooting

## Missing optional dependencies

### `ImportError` from `headroom.memory`

Typical causes:

- Memory extras were not installed.
- The selected backend needs optional vector or embedder dependencies.
- The environment has the package but not the backend runtime you selected.

What to do:

1. Start with the simplest local path: `Memory()` or `LocalBackend(..., embedder_backend="onnx")`.
2. If that still fails, inspect the installed package set for the memory extra rather than switching to service-backed memory immediately.
3. Do not add Qdrant/Neo4j or OpenAI credentials just to prove the local path works.

### `MemoryConfig` validation errors

Common messages and fixes:

- `openai_api_key is required when using OpenAI embedder backend` — pass the key or choose a local embedder backend.
- Vector backend unavailable — install `sqlite-vec` or `hnswlib`, or leave `VectorBackend.AUTO` and satisfy one of the local options.
- External backend name missing — provide the registered entry-point name for `StoreBackend.EXTERNAL`, `VectorBackend.EXTERNAL`, or `TextBackend.EXTERNAL`.

## Local database confusion

### `headroom memory list` shows nothing

Usually the CLI is looking at the wrong database.

- Confirm whether the current project has `.headroom/memory.db`.
- Pass `--db-path` explicitly during debugging.
- Remember the default store is the project store if present, otherwise the global workspace memory database.

### Two projects appear to share data

That means they probably point at the same database path.

- Give each project its own `db_path`.
- Avoid using a globally shared file for app-specific memory unless you explicitly want cross-project sharing.

### Memory file locked or stale

If a delete, prune, purge, or repair step fails:

- Stop any process holding the database open.
- Make sure the target path is not mounted read-only.
- Retry the command only after confirming the correct database path.

## Search, retrieval, and supersession issues

### Search returns superseded or stale memories

- Use the `show` command or `Memory.get_history()` to inspect the lineage.
- `repair-supersession` is only for one known bad reciprocal edge.
- If a new memory was supposed to replace an old one, prefer a clean supersession through the API rather than manual row edits.

### `memory delete` or `memory prune` removed the wrong rows

Recovery options:

1. Re-import from a recent `memory export` backup if available.
2. Rebuild the desired entries through the source conversation or application state.
3. If you exported before cleanup, re-run import into a fresh database and compare counts before replacing the live file.

### `headroom_retrieve` says the hash is missing or expired

- Expired hashes are terminal for that hash value. Re-run the command, re-read the file, or repeat the source step that produced the marker.
- Do not keep retrying the same stale hash.
- If the content came from a file read, disk is the source of truth; if it came from command output, re-run the command.
- Proxy-backed retrieval and local MCP-store retrieval have different TTL lifetimes; check which source created the hash.

## MCP registration and host setup

### MCP tools are not visible in the host

- Run `headroom mcp status`.
- If the agent is missing, reinstall for that agent name.
- Restart the host after registration.
- Verify the host is configured to launch `headroom mcp serve`.

### Tool names look doubled

Seeing `mcp__headroom__headroom_retrieve` is correct. The double `headroom` comes from MCP server name + tool name namespacing.

### MCP status says configured but proxy is down

- Start the proxy in `proxy-wrap`.
- Confirm the proxy URL you registered is reachable from the host.
- If you use a custom proxy URL, make sure `headroom mcp install --proxy-url ...` and the live proxy match exactly.
- A broken proxy URL can also come from stale environment settings in the host's config. Reinstall with `--force` if needed.

### `mcp install` appears to succeed but the agent still cannot start the server

- The host may not see the `headroom` executable on PATH.
- Re-register with a command path that the host can actually execute.
- For CLI-managed agents, check their own config conventions rather than assuming every agent reads the same file.

## `headroom learn` problems

### `No LLM API key found`

`headroom learn` needs one of:

- an API-key-backed model,
- a supported local CLI backend,
- or an explicit `--model`.

Fix the model selection before assuming the transcript parser is broken.

### `--verbosity` writes a file but nothing changes

The verbosity profile alone is not enough.

- The proxy must see output shaping enabled.
- `--apply` tries to hot-enable a running proxy; otherwise set `HEADROOM_OUTPUT_SHAPER=1` for the next proxy start or wrap.
- If you only changed the file in the workspace, a currently running proxy may still be using its previous environment.

### The chosen verbosity looks wrong

- Check whether the project had enough transcript data.
- Use the dry-run output to inspect interrupt and fast-skip signals.
- If the source agent is not Claude Code, verbosity mode may not be available.

## Codex recovery issues

### `headroom recover codex` finds nothing

Possible reasons:

- No retained temporary Codex homes exist.
- The temp home was already deleted.
- The active Codex home lacks durable history to merge.

If the command reports indexed chats, resume in Codex and review all working directories.

### Recovery fails mid-way

The recovery flow is transactional and keeps a backup. If it aborts:

- Leave the backup directory alone.
- Re-run with the same source and target only after understanding the conflict.
- Do not manually merge partial files from the failed attempt.

## Direct API troubleshooting tips

- Prefer `LocalBackend` plus `embedder_backend="onnx"` for lightweight local proofs.
- Call `await close()` on `Memory`, `HierarchicalMemory`, and `LocalBackend` when done.
- If `with_memory` appears to hang inside an async app, switch to the explicit async API or `with_memory_tools.acreate`.
- If the wrapper saves the wrong scope, check the `user_id`, `session_id`, and `agent_id` values first.
- For tool-call loops, inspect `_memory_tool_results` on the response and verify the model actually called a memory tool.
