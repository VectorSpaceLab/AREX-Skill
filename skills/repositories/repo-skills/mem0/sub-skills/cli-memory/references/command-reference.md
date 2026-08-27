# Mem0 CLI Command Reference

This reference covers the Mem0/mem0ai `mem0` terminal command as implemented by the Python `mem0-cli` package and the Node `@mem0/cli` package. Both implementations are intended to expose the same command surface and output formats.

## Installation And Runtime Choice

| Runtime | Package | Minimum runtime | Installs | Best fit |
| --- | --- | --- | --- | --- |
| Python | `mem0-cli` | Python `3.10+` | `mem0` | Python-first machines, `pipx`, virtualenvs, CI images with Python |
| Node | `@mem0/cli` | Node `18+` | `mem0` | JavaScript/TypeScript projects, npm-global tools, agent shells with Node |

Use whichever runtime is already available. Do not install both into the same global PATH unless you are intentionally testing parity, because the last-installed binary may shadow the other.

## Global And Connection Options

| Option | Meaning | Notes |
| --- | --- | --- |
| `--json`, `--agent` before a command | Agent/programmatic envelope output | In Node, global `--agent` must be placed before most subcommands: `mem0 --agent search ...`. For `init`, `mem0 init --agent` means Agent Mode bootstrap, not just JSON output. |
| `--api-key <key>` | Per-command API key override | Highest precedence. Avoid putting secrets in shell history when possible. |
| `--base-url <url>` | Per-command Platform API URL override | Defaults to `https://api.mem0.ai` unless overridden by env/config. |
| `--version` | Print CLI version | Top-level option. |
| `-o, --output <format>` | Command-specific output format | Use `--agent` for uniform envelopes; `--output json` may be raw API/list JSON for some commands. |

## Scope Flags

Most memory commands can scope by entity:

| Flag | Scope |
| --- | --- |
| `-u, --user-id <id>` | User |
| `--agent-id <id>` | Agent |
| `--app-id <id>` | App |
| `--run-id <id>` | Run |

Resolution rule: if any explicit scope flag appears, the CLI uses only explicitly supplied scope IDs and does not mix in defaults from config for the omitted scope types. If no explicit scope flags appear, configured defaults are used.

## Command Matrix

| Command | Purpose | Default output | Output formats | Backend needed |
| --- | --- | --- | --- | --- |
| `mem0 init` | Configure API key, email login, or Agent Mode bootstrap | human/agent-specific | text, JSON for agent flow | No existing config required |
| `mem0 identify` | Tag an active Agent Mode key with an agent name | text | text/agent behavior depends on implementation state | Yes |
| `mem0 whoami` | Print active AGENTRUSH identifier | text | text | Config-dependent |
| `mem0 agent-rush add/search` | AGENTRUSH game commands | text | text | Yes |
| `mem0 add` | Add memory from text, messages JSON, file, or stdin | text | `text`, `json`, `quiet`, `agent` | Yes |
| `mem0 search` | Semantic/keyword/hybrid memory search | text | `text`, `json`, `table`, `agent` | Yes |
| `mem0 list` | List memories with filters and pagination | table | `text`, `json`, `table`, `agent` | Yes |
| `mem0 get` | Retrieve one memory by ID | text | `text`, `json`, `agent` | Yes |
| `mem0 update` | Update memory text and/or metadata | text | `text`, `json`, `quiet`, `agent` | Yes |
| `mem0 delete` | Delete one memory, matching memories, or an entity | text | `text`, `json`, `quiet`, `agent` | Yes |
| `mem0 import` | Bulk import memories from local JSON | text | `text`, `json`, `agent` | Yes |
| `mem0 config show/get/set` | Inspect or edit local CLI config | text | show supports `json`/`agent`; get/set also support agent envelope when agent mode is active | No network for local config reads/writes |
| `mem0 entity list/delete` | List or cascade-delete Platform entities | table/text | `table`, `json`, `quiet`, `agent` depending on subcommand | Yes |
| `mem0 event list/status` | Inspect background processing events | table/text | `table`, `json`, `agent` | Yes |
| `mem0 status` | Check auth/connectivity and current backend | text | `text`, `json`, `agent` | Yes |
| `mem0 help --json` | Machine-readable CLI command tree when packaged spec is present | JSON | JSON | No |

## `mem0 init`

Use `init` to create or update `~/.mem0/config.json`.

Common forms:

```bash
mem0 init
mem0 init --api-key "$MEM0_API_KEY" --user-id alice --force
mem0 init --email alice@example.com
mem0 init --email alice@example.com --code 482901
mem0 init --agent --agent-caller codex --json
```

Important distinctions:

- `mem0 init --agent` is the unattended Agent Mode bootstrap flow. It can create an unclaimed agent-mode key without an email address.
- `mem0 --agent init ...` is global JSON-output mode around the `init` command.
- `mem0 init --agent --json` is the documented agent bootstrap plus JSON envelope form.
- `--force` skips overwrite confirmation when config already exists.
- `--email` and `--code` implement non-interactive email-code login when both are supplied.
- `--source` is attribution metadata for signup channels.

After an Agent Mode bootstrap without `--agent-caller`, use:

```bash
mem0 identify codex
```

## `mem0 add`

Usage:

```bash
mem0 add [text] [--user-id ID] [--messages JSON] [--file PATH] [--metadata JSON]
```

Primary options:

| Option | Meaning |
| --- | --- |
| `text` | Text memory content. |
| `--messages <json>` | Conversation messages as a JSON array, sent as messages rather than plain text. |
| `-f, --file <path>` | Read messages/content JSON from a local file. |
| `-m, --metadata <json>` | Attach metadata object. Must parse as JSON. |
| `--immutable` | Prevent future updates to this memory where supported by the backend. |
| `--no-infer` | Store raw text instead of fact extraction/inference. Node Commander maps this internally as `infer=false`, but users should use `--no-infer`. |
| `--expires YYYY-MM-DD` | Expiration date; must match `YYYY-MM-DD` and be in the future. |
| `--categories <value>` | JSON array or comma-separated category list. |
| `--graph`, `--no-graph` | Spec-level graph extraction toggles. Check installed CLI help for implementation support before relying on them in automation. |
| `-o, --output text,json,quiet` | Human, raw JSON, or no normal output. |

Input priority is `--file` first, then `--messages`, then text argument, then stdin when stdin is a pipe/file and agent mode is not active.

Examples:

```bash
mem0 add "User prefers dark mode" --user-id alice
mem0 add --messages '[{"role":"user","content":"I use vim"}]' --user-id alice
mem0 add --file conversation.json --user-id alice --output json
printf '%s\n' "User likes high-contrast themes" | mem0 add --user-id alice
mem0 add "Store exactly this sentence" --user-id alice --no-infer --metadata '{"source":"cli"}'
```

Add results may include events: `ADD`, `UPDATE`, `DELETE`, `NOOP`, or `PENDING`. Duplicate `PENDING` entries sharing an event ID are deduplicated before output.

## `mem0 search`

Usage:

```bash
mem0 search [query] [--user-id ID] [--top-k N] [--threshold SCORE]
```

Options:

| Option | Meaning |
| --- | --- |
| `query` | Search query; falls back to piped stdin when absent. |
| `-k, --top-k, --limit <n>` | Number of results, default `10`, must be `>= 1`. |
| `--threshold <score>` | Similarity score threshold, default `0.3`, must be `0.0` to `1.0`. |
| `--rerank` | Request reranking where supported by the Platform. |
| `--keyword` | Use keyword search instead of semantic search. |
| `--filter <json>` | Advanced filter expression as JSON. Must parse locally before request. |
| `--fields <list>` | Comma-separated fields to return. |
| `--graph`, `--no-graph` | Spec-level graph search toggles; verify help support in the installed CLI. |
| `-o, --output text,json,table` | Human text, raw JSON, or table. |

Examples:

```bash
mem0 search "preferences" --user-id alice
mem0 search "preferred editor" --user-id alice --top-k 5 --threshold 0.4 --output json
mem0 search "deployment context" --agent-id ci-bot --keyword
printf '%s' "dietary restrictions" | mem0 search --user-id alice --output table
```

## `mem0 list`

Usage:

```bash
mem0 list [scope/options]
```

Options:

| Option | Meaning |
| --- | --- |
| `--page <n>` | Page number, default `1`, must be `>= 1`. |
| `--page-size <n>` | Results per page, default `100`, must be `>= 1`. |
| `--category <name>` | Filter by category. |
| `--after YYYY-MM-DD` | Filter memories created after date. |
| `--before YYYY-MM-DD` | Filter memories created before date. |
| `--graph`, `--no-graph` | Spec-level graph filter toggle; verify installed support. |
| `-o, --output text,json,table` | Table is default. |

Examples:

```bash
mem0 list --user-id alice
mem0 list --user-id alice --category preferences --output json
mem0 list --agent-id ci-bot --page 2 --page-size 50
```

## `mem0 get`

Usage:

```bash
mem0 get <memory_id> [--output text|json]
```

Use this after extracting an ID from `search`, `list`, or an agent-mode envelope.

## `mem0 update`

Usage:

```bash
mem0 update <memory_id> [text] [--metadata JSON]
```

Rules:

- New text may come from positional text or stdin.
- Metadata must be JSON.
- Supplying neither text nor metadata is a misuse; check current installed behavior and prefer explicit text/metadata in scripts.

Examples:

```bash
mem0 update "$MEMORY_ID" "User now prefers light mode" --output json
printf '%s' "Updated: prefers dark mode and high contrast" | mem0 update "$MEMORY_ID"
mem0 update "$MEMORY_ID" --metadata '{"priority":"high"}'
```

## `mem0 delete`

`delete` has mutually exclusive modes:

| Mode | Example | Safety |
| --- | --- | --- |
| Single memory | `mem0 delete <memory_id>` | Use `--dry-run` first if unsure. |
| Matching memories | `mem0 delete --all --user-id alice --force` | Destructive; in agent mode requires `--force`. |
| Project-wide memories | `mem0 delete --all --project --force` | Very destructive; `--dry-run` is not a reliable count for project-wide API wildcard deletion. |
| Entity cascade | `mem0 delete --entity --user-id alice --force` | Deletes entity and all linked memories. |

Examples:

```bash
mem0 delete "$MEMORY_ID" --dry-run
mem0 delete "$MEMORY_ID" --force
mem0 delete --all --user-id alice --dry-run
mem0 delete --all --user-id alice --force
mem0 delete --entity --agent-id old-agent --force
```

Never combine `<memory_id>`, `--all`, and `--entity`; the CLI rejects mixed modes.

## `mem0 import`

Usage:

```bash
mem0 import <file_path> [--user-id ID] [--agent-id ID]
```

The file should be a JSON array or object. Each item can use `memory`, `text`, or `content` for the memory content, with optional per-item `user_id`, `agent_id`, and `metadata`. CLI-provided `--user-id` or `--agent-id` overrides item values.

Example file:

```json
[
  { "memory": "Prefers dark mode", "metadata": { "source": "intake" } },
  { "text": "Uses vim keybindings", "user_id": "alice" }
]
```

Safe preflight:

```bash
python scripts/validate_cli_json.py import-file memories.json
mem0 import memories.json --user-id alice --output json
```

## `mem0 config`

Subcommands:

```bash
mem0 config show
mem0 config show --output json
mem0 config get defaults.user_id
mem0 config set defaults.user_id alice
mem0 config set platform.base_url https://api.mem0.ai
```

Known key aliases include `api_key`, `base_url`, `user_email`, `user_id`, `agent_id`, `app_id`, and `run_id`, plus dotted forms such as `platform.api_key` and `defaults.user_id`. Displayed API keys are redacted.

## `mem0 entity`

Examples:

```bash
mem0 entity list users --output json
mem0 entity list agents
mem0 entity delete --user-id alice --dry-run
mem0 entity delete --user-id alice --force
```

Valid list entity types are `users`, `agents`, `apps`, and `runs`. Entity delete requires at least one scope flag and cascades to all memories for the entity.

## `mem0 event`

Use events when `add`, bulk deletes, or other operations report background processing.

```bash
mem0 event list --output json
mem0 event status <event-id> --output json
```

Event status can include fields such as event ID, type, status (`PENDING`, `PROCESSING`, `SUCCEEDED`, `FAILED`), latency, timestamps, and per-memory results.

## `mem0 status`

Use for connectivity checks and CI smoke tests:

```bash
mem0 status
mem0 --agent status
mem0 status --output json
```

Agent/json output includes connection state, backend, base URL, and duration. Do not treat status success as proof a later write will succeed; scoped add/search operations can still fail due to invalid filters, missing permissions, or backend feature support.

## Command Parity Notes

- The Python and Node implementations are tested with mirrored command and Agent Mode tests.
- Both implementations use the same config file path and environment variable names.
- Both disable stdin fallback in agent mode, so scripts should pass text/query explicitly when using `--agent`.
- Node has extra nuance around `--agent`: global JSON alias belongs before the subcommand, while `init --agent` is the bootstrap flag.
- The checked CLI spec contains `--graph` and `--no-graph` for add/search/list, but live command handlers may lag. Confirm with `mem0 <command> --help` before using graph flags in production automation.
