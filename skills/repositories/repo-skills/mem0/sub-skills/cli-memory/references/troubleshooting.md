# Mem0 CLI Troubleshooting

Use this guide for Mem0/mem0ai terminal workflows with Python `mem0-cli` or Node `@mem0/cli`.

## Quick Triage

| Symptom | Likely cause | Safe next step |
| --- | --- | --- |
| `mem0: command not found` | CLI package not installed or PATH shadowing. | Install one runtime package or run the package-specific module/dev command; verify `which mem0`. |
| Wrong CLI implementation/version | Both Python and Node installed; PATH resolves unexpected binary. | `mem0 --version`, `which mem0`, `python -m mem0_cli --version` where applicable, `npm bin -g`/package manager info. |
| `No API key configured.` | Missing config and `MEM0_API_KEY`. | Run `mem0 init` or set `MEM0_API_KEY`; see `configuration.md`. |
| Auth failure | Invalid/expired API key or env var overriding stored key. | Check `mem0 config show`, unset `MEM0_API_KEY` temporarily, run `mem0 status`. |
| JSON parser fails | Used human/text output or spinners/colors on stdout. | Use `mem0 --agent <command>` and validate with `scripts/validate_cli_json.py`. |
| Search returns empty after add | Add may be async/PENDING, wrong scope, threshold too high, or filter mismatch. | Check add result/event ID, `mem0 event status`, agent-mode `scope`, lower `--threshold`. |
| Defaults seem ignored | Any explicit scope flag disables mixing in other defaults. | Inspect agent-mode `scope`; pass all intended scope IDs explicitly. |
| `Invalid JSON in --metadata`, `--messages`, or `--filter` | Shell quoting or malformed JSON. | Validate with `python -m json.tool` or `scripts/validate_cli_json.py`. |
| Delete rejected in agent mode | Destructive all/entity operation requires `--force`. | Run `--dry-run` first when possible, then add `--force` intentionally. |
| `--graph` rejected or ineffective | Spec/docs and installed binary do not match, or graph is a backend/provider topic. | Check `mem0 <command> --help`; route provider/backend graph setup to `provider-configuration`. |

## Install And Import Problems

### Python CLI

Facts: package `mem0-cli`, Python `>=3.10`, entry point `mem0 = mem0_cli.app:main`.

Recommended install:

```bash
pipx install mem0-cli
```

Alternative inside a virtual environment:

```bash
python -m pip install mem0-cli
python -m mem0_cli --help
```

Common issues:

- macOS/Homebrew Python may reject global `pip install` due to externally managed environments; use `pipx` or a venv.
- Python `3.9` or older is unsupported for the CLI even if the core SDK supports older Python versions.
- If `mem0` points to Node after installing Python, inspect PATH ordering rather than reinstalling blindly.

### Node CLI

Facts: package `@mem0/cli`, Node `>=18`, ESM binary `dist/index.js`.

Install:

```bash
npm install -g @mem0/cli
mem0 --help
```

Common issues:

- Node older than `18` is unsupported.
- Global npm bin directory may not be on PATH.
- If a local repo checkout is used for development, run package scripts from that package root; normal users should use the published package.

## Authentication And Config

### Missing Key

Message:

```text
No API key configured.
```

Fix:

```bash
mem0 init
# or
export MEM0_API_KEY="m0-..."
mem0 status
```

### Invalid Or Expired Key

Message may mention invalid/expired API key or authentication failure.

Checks:

```bash
mem0 config show
mem0 status --output json
```

If a good stored key appears to be ignored, check whether `MEM0_API_KEY` is set to a bad value. Environment overrides config.

### Wrong Base URL

If status shows a custom host or network error:

```bash
mem0 status --output json
unset MEM0_BASE_URL
mem0 status --output json
```

Only use `--base-url`/`MEM0_BASE_URL` when the user has a compatible hosted or self-hosted endpoint. For self-hosted deployment diagnosis, route to `../self-hosted-openmemory/SKILL.md`.

## Agent Mode And JSON Failures

### Output Is Not JSON

Use global agent mode before the subcommand:

```bash
mem0 --agent search "preferences" --user-id alice
```

Special `init` form:

```bash
mem0 init --agent --agent-caller codex --json
```

Validate:

```bash
mem0 --agent status | python scripts/validate_cli_json.py agent-envelope -
```

### Error JSON Has No Expected Data

In agent mode, failures use `status: "error"` and may set `data: null`. Always branch on `.status` before reading `.data`:

```bash
result=$(mem0 --agent search "preferences" --user-id alice)
status=$(printf '%s' "$result" | jq -r '.status')
if [ "$status" != "success" ]; then
  printf '%s\n' "$result" | jq -r '.error' >&2
  exit 1
fi
```

### Stdin Does Not Work In Agent Mode

The checked implementations disable stdin fallback in agent mode. Pass content explicitly or use `--file`/`--messages`:

```bash
mem0 --agent add "User prefers dark mode" --user-id alice
mem0 --agent add --file conversation.json --user-id alice
```

## Data And JSON Validation

### Bad Metadata

Use single quotes around JSON in POSIX shells:

```bash
mem0 add "Uses vim" --user-id alice --metadata '{"source":"cli"}'
```

Validate locally:

```bash
printf '%s\n' '{"source":"cli"}' | python -m json.tool >/dev/null
```

### Bad Messages File

Expected messages file is usually a JSON array of message objects:

```json
[
  { "role": "user", "content": "I use vim" },
  { "role": "assistant", "content": "Noted." }
]
```

Validate:

```bash
python scripts/validate_cli_json.py messages conversation.json
```

### Bad Import File

Each item needs `memory`, `text`, or `content`:

```bash
python scripts/validate_cli_json.py import-file memories.json
```

Items without content are skipped/failed by import accounting.

### Bad Filter JSON

`--filter` must parse as JSON before the request is made:

```bash
mem0 search "preferences" --user-id alice --filter '{"categories":{"contains":"food"}}'
```

If the API rejects a semantically valid JSON filter, route exact filter syntax/API shape to `../sdk-memory/SKILL.md` because it owns SDK/API memory operation semantics.

## Scope And Defaults

Problem: command searches or deletes the wrong set of memories.

Checklist:

1. Run `mem0 config show --output json` and note configured defaults.
2. Check env vars: `MEM0_USER_ID`, `MEM0_AGENT_ID`, `MEM0_APP_ID`, `MEM0_RUN_ID`.
3. Inspect the agent-mode `scope` field from the failing command.
4. If using any explicit scope flag, pass every intended scope flag explicitly.

Example fix:

```bash
# Ambiguous if config has defaults you forgot about.
mem0 search "preferences"

# Explicit and reproducible.
mem0 --agent search "preferences" --user-id alice --agent-id support-bot
```

## Add/Search Timing

`mem0 add` may return `PENDING` entries with an `event_id` when processing continues in the background. Searching immediately can return empty.

Fix:

```bash
add=$(mem0 --agent add "User prefers dark mode" --user-id alice)
event_id=$(printf '%s' "$add" | jq -r '.data[]? | .event_id // empty' | head -n1)
if [ -n "$event_id" ]; then
  mem0 --agent event status "$event_id"
fi
sleep 2
mem0 --agent search "dark mode" --user-id alice --threshold 0.1
```

Also check:

- same scope IDs for add and search;
- `--threshold` not too high;
- `--keyword` vs semantic search intent;
- `--filter`/`--category` not excluding the memory;
- backend/API errors hidden by a wrapper script.

## Delete And Entity Safety

### Mixed Modes

The CLI rejects combinations of memory ID, `--all`, and `--entity`.

Use exactly one:

```bash
mem0 delete "$MEMORY_ID"
mem0 delete --all --user-id alice --force
mem0 delete --entity --user-id alice --force
```

### Agent Mode Requires Force

For all/entity destructive operations:

```bash
mem0 delete --all --user-id alice --dry-run
mem0 --agent delete --all --user-id alice --force
```

Do not automate interactive confirmations. Use `--dry-run` plus explicit `--force`.

### Project-wide Delete

`mem0 delete --all --project --force` maps to wildcard project deletion. Treat it as highly destructive. Do not run it unless the user explicitly asks for project-wide wipe and understands that dry-run may not provide a reliable project-wide count.

## Events And Background Operations

If output says queued or deletion started:

```bash
mem0 event list
mem0 event status <event-id>
mem0 --agent event status <event-id>
```

If events fail with a platform capability error, the endpoint may require hosted Platform support or account permissions.

## Graph Flags And Tri-state

Graph evidence is split:

- CLI spec/docs list `MEM0_ENABLE_GRAPH`, `--graph`, and `--no-graph` for add/search/list.
- Some live command handlers/help builders list graph options, but core command signatures may not pass graph flags in all versions.

Debug path:

```bash
mem0 add --help | grep -E -- '--graph|--no-graph' || true
mem0 search --help | grep -E -- '--graph|--no-graph' || true
mem0 help --json | python scripts/summarize_cli_spec.py - --format markdown
```

If installed CLI rejects the flag, do not force it; use the version-supported CLI or route provider/graph backend configuration to `../provider-configuration/SKILL.md`.

## Optional Dependencies And Backend Features

The CLI talks to the hosted Platform API and does not require local vector stores, embedders, LLMs, graph databases, or rerankers for normal CLI usage. If an error mentions optional OSS dependencies, vector stores, provider imports, embedding dimensions, Neo4j/Qdrant, or local `Memory()` configuration, the task likely belongs to `../provider-configuration/SKILL.md` or `../self-hosted-openmemory/SKILL.md`.

## Command Parity Drift

Because Python and Node packages are independent releases, a user may see parity drift.

Check:

```bash
mem0 --version
mem0 help --json
mem0 add --help
mem0 search --help
```

If debugging package source, compare behavior against mirrored CLI tests conceptually: command tests, config tests, and agent-mode tests exist for both Python and Node. Do not ask future agents to run original repo tests from this runtime skill; use installed help/spec and the bundled read-only scripts instead.

## Escalation Routes

- SDK/API payload semantics, filters, exports/feedback: `../sdk-memory/SKILL.md`.
- Provider/backend/graph/vector/LLM configuration: `../provider-configuration/SKILL.md`.
- Self-hosted deployment, OpenMemory, Docker, REST server, MCP server: `../self-hosted-openmemory/SKILL.md`.
- Editor plugins, hooks, slash commands, MCP agent plugin setup: `../integrations-plugins/SKILL.md`.
