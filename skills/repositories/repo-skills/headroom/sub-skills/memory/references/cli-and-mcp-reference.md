# Memory CLI and MCP reference

## Memory database selection

Most `headroom memory` commands accept `--db-path PATH`.

Default resolution:

1. If the current project has `.headroom/memory.db`, use it.
2. Otherwise use the Headroom workspace memory database.

For audits, pass `--db-path` explicitly so you do not inspect or mutate the wrong store.

## `headroom memory` commands

### List

```bash
headroom memory list
headroom memory list --db-path ./memory.db --limit 10
headroom memory list --scope USER
headroom memory list --session sess-123
headroom memory list --since 7d
headroom memory list --search "api"
```

- `--limit` / `-n`: maximum rows, minimum `1`, default `50`.
- `--scope`: one of `USER`, `SESSION`, `AGENT`, `TURN` (case-insensitive).
- `--since`: duration such as `7d`, `2w`, or `1m`.
- `--search` / `-q`: SQL `LIKE` content search; structured filters are applied after the content search.
- Output truncates memory IDs to an 8-character prefix for display.

### Show

```bash
headroom memory show <memory-id>
headroom memory show <memory-id-prefix> --json
```

- Exact IDs are preferred; unambiguous prefixes are accepted.
- Ambiguous prefixes fail and print matching prefixes.
- `--json` emits the full serialized memory, including lineage, metadata, and embedding when present.

### Stats

```bash
headroom memory stats
headroom memory stats --db-path ./memory.db
```

Reports total memory count, database size, scope counts, age buckets, oldest age, and average importance.

### Edit

```bash
headroom memory edit <memory-id> --content "Updated content"
headroom memory edit <memory-id> --importance 0.8
headroom memory edit <memory-id> -c "Updated" -i 0.9
```

- At least one of `--content` or `--importance` is required.
- `--importance` must be between `0.0` and `1.0`.
- Prefix matching follows the same rules as `show`.

### Repair supersession

```bash
headroom memory repair-supersession <old-id> <new-id>
headroom memory repair-supersession <old-id> <new-id> --apply
```

This detaches exactly one reciprocal lineage edge where `old.superseded_by == new.id` and `new.supersedes == old.id`.

- Default is a dry run that prints the planned repair.
- `--apply` clears the old memory's `valid_until` and `superseded_by`, clears the new memory's `supersedes`, and refreshes indexes through the local backend.
- Stop any proxy or writer using the same database before applying a repair.

### Delete

```bash
headroom memory delete <id> --force
headroom memory delete <id1> <id2> --force
```

- Deletes one or more exact or unambiguous prefix IDs.
- Prompts unless `--force` / `-f` is set.
- Missing IDs are warned and skipped; ambiguous prefixes fail.

### Prune

```bash
headroom memory prune --older-than 30d --dry-run
headroom memory prune --scope TURN --force
headroom memory prune --low-importance 0.3 --force
headroom memory prune --older-than 7d --scope TURN --session sess-123 --force
```

- Requires at least one filter: `--older-than`, `--scope`, or `--low-importance`.
- Filters combine with AND logic.
- `--dry-run` prints what would be removed without deleting.
- `--force` skips the confirmation prompt.

### Purge

```bash
headroom memory purge --confirm
```

Deletes all memories in the selected database. The command requires `--confirm` and then prompts once more. Use only after confirming `--db-path`.

### Export and import

```bash
headroom memory export
headroom memory export --output backup.json
headroom memory import backup.json --force
```

- Export emits a JSON array of memory objects as serialized by Headroom.
- Import expects that array format. Existing memories with the same ID are replaced.
- Malformed entries are skipped and reported.
- Use export before destructive edits or supersession repair.

## `headroom mcp` commands

The `headroom mcp` CLI manages the Headroom CCR MCP server. The server exposes context engineering tools, not the persistent memory CRUD CLI.

### Install

```bash
headroom mcp install
headroom mcp install --agent claude
headroom mcp install --agent codex --agent opencode
headroom mcp install --proxy-url http://127.0.0.1:8787
headroom mcp install --proxy-url http://127.0.0.1:9000 --force
```

- Requires the MCP SDK; if missing, install Headroom with the MCP extra.
- By default, installs into every detected supported agent.
- `--agent NAME` restricts installation; repeat it to install into multiple specific agents.
- `--proxy-url` is stored as `HEADROOM_PROXY_URL` only when it differs from the default.
- `--force` overwrites mismatched Headroom-owned registrations where the registrar allows safe replacement.
- Next steps after install: start the proxy if proxy-backed retrieval is desired, then restart the agent so it reloads MCP configuration.

### Status

```bash
headroom mcp status
```

Checks:

- MCP SDK importability.
- Whether each supported detected agent has a `headroom` MCP server configured.
- Effective proxy URL from the registered server environment.
- Proxy reachability at the configured URL.

A configured MCP server with an unreachable proxy can still provide local `headroom_compress`; proxy-backed `headroom_retrieve` and proxy stats will fail or warn until the proxy is running.

### Uninstall

```bash
headroom mcp uninstall
```

Removes `headroom` and legacy `codebase-memory-mcp` server registrations from detected supported agents. Other MCP servers are preserved.

### Serve

```bash
headroom mcp serve
headroom mcp serve --debug
HEADROOM_PROXY_URL=http://127.0.0.1:9000 headroom mcp serve
headroom mcp serve --proxy-url http://127.0.0.1:9000
headroom mcp serve --transport http --host 127.0.0.1 --port 8788 --path /mcp
```

- Default transport is stdio; this is the mode most MCP hosts launch.
- HTTP transport is Streamable HTTP and defaults to `127.0.0.1:8788/mcp`.
- `--proxy-url` or `HEADROOM_PROXY_URL` controls the proxy used for retrieval fallback and proxy stats.
- `--direct` is deprecated and ignored; retrieval uses local MCP store first and proxy URL fallback.
- `--debug` logs diagnostic output to stderr so stdout remains reserved for MCP protocol in stdio mode.

## MCP tool names and namespace display

The CCR MCP server is named `headroom` and exposes tools:

- `headroom_compress`: compress content on demand and store the original for retrieval.
- `headroom_retrieve`: retrieve full original content by `hash`.
- `headroom_stats`: report window-scoped session stats, local MCP compression/retrieval counts, subagent aggregation, and proxy/lifetime savings when available.
- `headroom_read`: optional file-read caching tool, enabled only when `HEADROOM_MCP_READ` is on.

MCP clients commonly display tools as `mcp__<server>__<tool>`. Therefore Claude Code may show `mcp__headroom__headroom_retrieve`. The doubled `headroom` is normal MCP namespacing, not a broken registration. Compression markers and prompts still refer to the bare tool name `headroom_retrieve`.

## CCR retrieve behavior

`headroom_retrieve` takes only a `hash` argument in the MCP tool schema.

Retrieval order:

1. Check the MCP process's local compression store. This covers content compressed through `headroom_compress` in the same session and content stored through the shared in-process store.
2. If local lookup misses and proxy checking is enabled, POST to the configured proxy retrieval endpoint.
3. Return the original content and source (`local` or `proxy`) when found.
4. If an entry expired, return terminal guidance: do not retry the same hash; re-run the command, re-read the file, or regenerate the source content.
5. If a hash was never stored or cannot be found, return a missing-content error and recovery hint.

The proxy injects `headroom_retrieve` into provider requests when compressed markers exist, and keeps the tool available for sessions that have already done CCR so later turns can redeem prior markers. Anthropic and OpenAI proxy paths resolve CCR tool calls server-side. Gemini-native paths have more limitations; use Anthropic/OpenAI proxy paths when transparent CCR resolution is required.

TypeScript `HeadroomClient.retrieve(hash, { query })` calls the proxy retrieval API and can pass a search query to that HTTP endpoint. Do not assume the MCP `headroom_retrieve` tool supports `query`; its tool input is `hash` only.

## MCP registry registrars

`headroom.mcp_registry` abstracts agent-specific MCP registration with a common `ServerSpec(name, command, args, env)` and `MCPRegistrar` contract.

Supported registrars in this version:

| Registrar | Detects | Writes |
| --- | --- | --- |
| `claude` | Claude Code CLI or user config | Prefer Claude's `mcp add/remove` CLI at user scope, with JSON file fallback |
| `codex` | OpenAI Codex CLI home | Marker-delimited TOML block under `mcp_servers` |
| `grok` | Grok CLI home | Marker-delimited TOML block under `mcp_servers` |
| `opencode` | OpenCode binary or config directory | JSON `mcp` entry with `type: local`, command list, and `environment` |

Registrar safety rules:

- Registration is idempotent when the existing spec matches.
- A mismatched existing server is left untouched unless `--force` is supplied and the registrar can safely own that entry.
- User-managed TOML entries outside Headroom markers are not clobbered.
- Malformed JSON/TOML configs are preserved and registration fails with a repair message rather than overwriting other user settings.
- Uninstall removes only the named Headroom server entries and preserves unrelated MCP servers.

Programmatic helpers:

```python
from headroom.mcp_registry import build_headroom_spec, get_all_registrars, install_everywhere

spec = build_headroom_spec("http://127.0.0.1:8787")
results = install_everywhere(proxy_url="http://127.0.0.1:8787", agents=["claude"])
```

## Persistent memory MCP server

There is a separate module-level memory MCP server for native persistent memory tools:

```bash
python -m headroom.memory.mcp_server --db .headroom/memory.db --user alice
```

It exposes:

- `memory_search` with `query` and optional `top_k`.
- `memory_save` with an array of atomic `facts` and optional `importance`.

This server warms the embedder, re-indexes memories missing embeddings, filters superseded memories from search results, and records access metadata best-effort. It is not the same as `headroom mcp serve`, which exposes CCR compression/retrieval/stats tools.

## `headroom learn`

```bash
headroom learn
headroom learn --apply
headroom learn --all
headroom learn --agent codex --all
headroom learn --project . --agent claude --workers 4
headroom learn --target CLAUDE.md
headroom learn --main-only
```

- Default mode analyzes coding-agent session transcripts for failure patterns and writes recommendations only with `--apply`; otherwise it is a dry run.
- `--agent auto` scans detected plugins. Built-ins include `claude`, `codex`, `gemini`, and `grok`; external plugins use the `headroom.learn_plugin` entry point.
- Model auto-detection prefers API keys, then `HEADROOM_LEARN_CLI`, then installed `claude`, `gemini`, or `codex` CLIs.
- `--target` is honored only by writers that support target context files; unsupported agents print a note and ignore it.
- `--main-only` skips nested subagent/workflow transcripts where the selected plugin supports that distinction.

### Verbosity mode

```bash
headroom learn --verbosity
headroom learn --verbosity --apply
headroom learn --verbosity --apply --all
headroom learn --verbosity --llm-judge --model claude-sonnet-4-6
```

- Verbosity mode mines behavioral signals from Claude Code transcripts: interruptions, fast-skips, long-output frequency, and echo ratio.
- `--apply` writes a learned verbosity profile and seeds the output-savings baseline. It also tries to hot-enable the output shaper on a running local proxy; otherwise it prints the environment setting needed for the next proxy start or wrap.
- `--llm-judge` only applies with `--verbosity`; without it, the heuristic level is used.
- With `--verbosity`, flags such as `--target`, `--main-only`, non-judge `--model`, and `--workers` are ignored and called out.

## `headroom recover codex`

```bash
headroom recover codex
headroom recover codex --source <temporary-codex-home> --target <active-codex-home>
headroom recover codex --source <one> --source <two> --yes
```

Use when a Headroom Codex wrapper was interrupted and left sessions/config in temporary Codex homes.

Behavior:

- If `--source` is omitted, Headroom scans standard temp roots and retained recovery sources for non-empty temporary Codex homes.
- If `--target` is omitted, it uses `CODEX_HOME` or the default Codex home.
- Prints target and sources, then prompts unless `--yes` is provided.
- Backs up the current target and pins each source before merging.
- Merges config, session rollouts, JSONL history, and compatible SQLite databases transactionally.
- Quarantines malformed JSONL lines and skips runtime artifacts such as locks, sockets, and SQLite WAL/journal sidecars.
- If no recoverable source exists, audits durable Codex history where possible and suggests `codex resume --all` when indexed chats are present.

Do not delete reported backup directories until the user confirms recovered Codex sessions and config are intact.
