---
name: cli-and-agent-tools
description: "Helps agents use the Data Designer CLI, config subcommands,
  persona downloads, plugin catalog commands, and machine-readable agent
  introspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# CLI and Agent Tools

Use this sub-skill when a request is about the `data-designer` command line, local config state, persona downloads, plugin catalog lookup/install commands, or the `data-designer agent ...` introspection interface.

## What belongs here

- Root CLI shape, `--help`, `--version`, and lazy command groups.
- `config` commands: `list`, `providers`, `models`, `mcp`, `tools`, `reset`.
- `download personas` flags and managed persona state.
- `plugin` and `plugin catalog` command routing.
- `agent context`, `agent types`, `agent state model-aliases`, and `agent state persona-datasets`.
- CLI-to-controller/API mapping for `preview`, `create`, `validate`, and `check-models` without generation internals.
- Config file locations, `DATA_DESIGNER_HOME`, plugin catalog cache, managed-assets layout, and `--` script-argument forwarding.
- Troubleshooting for PATH issues, missing API keys, no usable model aliases, bad config paths/modules, run-config shape, non-TTY preview navigation, reset/delete caution, and network/storage-bound persona downloads.

## What stays elsewhere

- Config object fields and config authoring rules → `../config-authoring/SKILL.md`.
- Runtime generation behavior for `preview`, `create`, `validate`, and `check-models` → `../generation-runtime/SKILL.md`.
- Plugin implementation contracts, entry-point authoring, and plugin package internals → `../plugins-and-extensions/SKILL.md`.

## Read these first

- `references/cli-reference.md` for command tree, flags, examples, and CLI-to-API mapping.
- `references/agent-introspection.md` for `agent context`, `agent types`, and `agent state` output structure.
- `references/configuration-files.md` for the state directory, config YAML files, plugin cache, and managed assets.
- `references/troubleshooting.md` for predictable CLI failures and recovery steps.
- `scripts/capture_agent_context.py` when you need a repeatable snapshot from an installed CLI without depending on the source checkout.

## Typical workflows

1. Bootstrap a session with `data-designer agent context`; it includes live type catalogs, model alias state, persona state, and the agent command registry.
2. Use `data-designer agent state model-aliases` before model-backed validation, preview, create, or config edits.
3. Use `data-designer agent state persona-datasets` or `download personas --list` before relying on persona locale data.
4. Use `data-designer --help` and `references/cli-reference.md` for exact command names and flags.
5. Preserve config-script args after `--`; do not turn them into Data Designer CLI options.
6. When a task crosses into config schema, generation runtime, or plugin internals, follow the sibling links above rather than duplicating that material here.

## Fast decision hints

- Fresh or unknown environment: run `scripts/capture_agent_context.py` or `data-designer agent context` first.
- No model aliases usable: configure providers/API keys, then re-run `agent state model-aliases`.
- Persona request: treat installation as per-locale under managed assets.
- Plugin discovery/install request: this sub-skill owns command syntax; route deeper plugin design to `plugins-and-extensions`.
- `preview`/`create`/`check-models` request: this sub-skill owns CLI flags and mapping; route execution semantics to `generation-runtime`.
