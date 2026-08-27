# Agent And JSON Workflows

Use this guide when a future agent needs reliable Mem0 CLI output in shell scripts, CI jobs, or tool loops.

## Choose The Right JSON Mode

| Mode | Command shape | Output contract | Best use |
| --- | --- | --- | --- |
| Agent mode | `mem0 --agent <command> ...` or command-specific `--json` where supported | Standard envelope with `status`, `command`, optional `duration_ms`, `scope`, `count`, `error`, `data`, and optional `mem0_notice` | LLM/agent loops and scripts that need consistent success/error handling |
| Raw JSON output | `mem0 <command> --output json` | Command-specific JSON, often raw API/list data or an envelope for some utility commands | `jq` pipelines when you know the command’s raw shape |
| Human/table/text | default output or `--output table/text` | Rich tables, colors, status text, spinners | Human terminal use only |
| Quiet | `--output quiet` on supported write/delete commands | Minimal or no normal output | Batch jobs where exit code is enough |

Prefer agent mode for automation because errors are JSON and progress/spinner output is kept away from stdout.

## Agent Envelope Shape

Typical success:

```json
{
  "status": "success",
  "command": "search",
  "duration_ms": 134,
  "scope": { "user_id": "alice" },
  "count": 2,
  "data": [
    { "id": "mem-abc", "memory": "User prefers dark mode", "score": 0.97 }
  ]
}
```

Typical error:

```json
{
  "status": "error",
  "command": "search",
  "error": "Authentication failed. Your API key may be invalid or expired.",
  "data": null
}
```

Do not require every optional field. `duration_ms`, `scope`, `count`, `error`, and `mem0_notice` appear only when relevant.

## Global `--agent` Placement

Recommended portable forms:

```bash
mem0 --agent search "preferences" --user-id alice
mem0 --agent add "User prefers dark mode" --user-id alice
mem0 --agent list --user-id alice
mem0 --agent status
```

Special case:

```bash
mem0 init --agent --agent-caller codex --json
```

For `init`, command-level `--agent` means Agent Mode bootstrap. Global `mem0 --agent init` means JSON output wrapping, not necessarily bootstrap. Use the documented `mem0 init --agent --json` form when bootstrapping an unattended agent account.

## Shell-safe Init/Add/Search Flow

This pattern avoids printing secrets and produces parseable JSON:

```bash
set -euo pipefail
: "${MEM0_API_KEY:?set MEM0_API_KEY}"

mem0 init --api-key "$MEM0_API_KEY" --user-id alice --force >/dev/null

add_json=$(mem0 --agent add "User prefers dark mode and vim keybindings" --user-id alice)
python scripts/validate_cli_json.py agent-envelope - <<'JSON'
${add_json}
JSON

search_json=$(mem0 --agent search "editor preferences" --user-id alice --top-k 5)
printf '%s\n' "$search_json" | python scripts/validate_cli_json.py agent-envelope -
```

In real shell code, pipe variables rather than embedding heredoc substitutions:

```bash
add_json=$(mem0 --agent add "User prefers dark mode" --user-id alice)
printf '%s' "$add_json" | python scripts/validate_cli_json.py agent-envelope -
```

## Add From Stdin Or File

Stdin fallback is intentionally disabled in agent mode. For agent mode, pass content explicitly or use `--file`/`--messages`.

Human/raw mode stdin examples:

```bash
printf '%s' "User likes monospace fonts" | mem0 add --user-id alice
printf '%s' "project preferences" | mem0 search --user-id alice --output json
printf '%s' "Updated preference text" | mem0 update "$MEMORY_ID"
```

Agent-mode examples:

```bash
mem0 --agent add "User likes monospace fonts" --user-id alice
mem0 --agent add --messages '[{"role":"user","content":"I use vim"}]' --user-id alice
mem0 --agent add --file conversation.json --user-id alice
```

Pre-validate local files:

```bash
python scripts/validate_cli_json.py messages conversation.json
mem0 --agent add --file conversation.json --user-id alice
```

## Import And Export Workflows

There is no separate `export` command in the checked CLI. Export by listing/searching JSON and redirecting stdout.

Export all listed memories for a scope:

```bash
mem0 list --user-id alice --output json > alice-memories.json
python scripts/validate_cli_json.py raw-list alice-memories.json
```

Import memories:

```bash
python scripts/validate_cli_json.py import-file alice-memories.json
mem0 --agent import alice-memories.json --user-id alice
```

Import file shape:

```json
[
  { "memory": "Prefers dark mode", "metadata": { "source": "export" } },
  { "text": "Uses vim keybindings", "user_id": "alice" },
  { "content": "Likes Python", "agent_id": "assistant" }
]
```

When a CLI `--user-id` or `--agent-id` is supplied during import, it overrides the corresponding per-item field.

## `jq` Recipes For Raw JSON

Use raw `--output json` when the shape is known.

```bash
mem0 list --user-id alice --output json | jq -r '.[].id'
mem0 list --user-id alice --output json | jq '[.[] | select(.categories[]? == "preferences")]'
mem0 search "tools" --user-id alice --output json | jq '.[] | {id, memory, score}'
```

Agent envelope equivalent:

```bash
mem0 --agent search "tools" --user-id alice | jq '.data[] | {id, memory, score}'
```

## Poll Background Events

Add or delete operations can return queued/PENDING work with an event ID.

```bash
result=$(mem0 --agent add "Long conversation summary" --user-id alice)
event_id=$(printf '%s' "$result" | jq -r '.data[]? | select(.status == "PENDING") | .event_id' | head -n1)

if [ -n "$event_id" ] && [ "$event_id" != "null" ]; then
  mem0 --agent event status "$event_id"
fi
```

Also inspect recent events:

```bash
mem0 --agent event list
```

## Safe Delete Automation

Always dry-run scoped deletes when supported:

```bash
mem0 delete --all --user-id alice --dry-run
mem0 --agent delete --all --user-id alice --force
```

Agent mode rejects destructive all/entity operations unless `--force` is supplied. This is intentional; never work around it with interactive prompt automation.

For single-memory deletes, extract IDs explicitly:

```bash
mem0 --agent search "obsolete preference" --user-id alice \
  | jq -r '.data[].id' \
  | while IFS= read -r id; do
      [ -n "$id" ] || continue
      mem0 --agent delete "$id"
    done
```

## Config Debugging In Agent Mode

Show redacted config:

```bash
mem0 --agent config show
```

Compare effective scope:

```bash
mem0 --agent search "scope check"              # uses configured defaults
mem0 --agent search "scope check" --user-id a  # uses only explicit user_id=a
```

Check connection:

```bash
mem0 --agent status
```

## Graph Tri-state Debugging

Graph controls are version-sensitive because the CLI spec/docs list `--graph`, `--no-graph`, and `MEM0_ENABLE_GRAPH`, while installed handlers may not fully forward them. Use this decision path:

1. Run `mem0 help --json` or `mem0 <command> --help` and verify whether `--graph`/`--no-graph` appears for the installed binary.
2. Check whether config/env has `MEM0_ENABLE_GRAPH` or a graph default.
3. For one command, pass an explicit `--graph` or `--no-graph` and inspect agent-mode output or backend behavior.
4. If the request is about OSS graph providers/backends rather than CLI flags, route to `../provider-configuration/SKILL.md`.

Do not promise graph behavior solely from docs if the installed CLI rejects the flag.

## Validate CLI JSON Locally

Bundled helper examples:

```bash
mem0 --agent status | python scripts/validate_cli_json.py agent-envelope -
mem0 list --user-id alice --output json > memories.json
python scripts/validate_cli_json.py raw-list memories.json
python scripts/validate_cli_json.py import-file memories.json
python scripts/validate_cli_json.py config config.json
python scripts/validate_cli_json.py messages conversation.json
```

The validator is read-only and does not contact Mem0.

## Machine-readable Command Discovery

When the installed package includes the spec:

```bash
mem0 help --json > mem0-cli-spec.json
python scripts/summarize_cli_spec.py mem0-cli-spec.json --format markdown
```

If `mem0 help --json` returns only fallback metadata, use installed `mem0 <command> --help` for the exact binary and do not infer unsupported flags from older docs.

## CI Pattern

```bash
set -euo pipefail
: "${MEM0_API_KEY:?set MEM0_API_KEY}"
mem0 init --api-key "$MEM0_API_KEY" --user-id ci-bot --force >/dev/null
mem0 --agent status | python scripts/validate_cli_json.py agent-envelope -
mem0 --agent add "Build ${BUILD_NUMBER:-local} completed" --agent-id ci-bot \
  | python scripts/validate_cli_json.py agent-envelope -
```

Keep secrets out of logs by avoiding `set -x` around any command that could echo environment or config state.
