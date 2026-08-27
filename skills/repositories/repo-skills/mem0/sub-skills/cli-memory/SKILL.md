---
name: cli-memory
description: "Use for Mem0/mem0ai command-line memory workflows: Python or Node
  mem0 CLI install, init, Agent Mode, add/search/list/get/update/delete,
  import/export via JSON, config defaults, entities, events, stdin/files, graph
  flags, and shell-safe automation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cli-memory

Use this sub-skill when the task is about operating the Mem0 memory layer from a terminal rather than embedding SDK calls in application code.

Natural triggers include: "Mem0 CLI", "mem0 command line", "mem0ai terminal", "memory layer shell workflow", `mem0 init`, `mem0 add`, `mem0 search`, `mem0 list`, `mem0 config`, `mem0 import`, `mem0 --agent`, `mem0 --json`, `@mem0/cli`, `mem0-cli`, stdin/file import, JSON output, entity cleanup, event status, or debugging CLI defaults.

## Route First

- Use this sub-skill for Python `mem0-cli` and Node `@mem0/cli` workflows, command parity, config precedence, output contracts, safe scripting, and CLI troubleshooting.
- Use sibling `../sdk-memory/SKILL.md` for Python/TypeScript SDK call-site code, `MemoryClient`, `Memory`, async clients, or app integration logic.
- Use sibling `../provider-configuration/SKILL.md` for OSS provider/vector/embedding/LLM/reranker/graph backend configuration beyond CLI flags.
- Use sibling `../self-hosted-openmemory/SKILL.md` for self-hosted server, OpenMemory, Docker, REST server, MCP server, migrations, and operational deployment.
- Use sibling `../integrations-plugins/SKILL.md` for editor plugin slash commands, lifecycle hooks, MCP agent plugins, Vercel AI SDK, OpenClaw, Pi Agent, and framework integrations.

## Key Facts

- Both CLI packages install a `mem0` executable and target the hosted Mem0 Platform API by default.
- Python package facts from repo metadata: `mem0-cli` version `0.2.8`, Python `>=3.10`, Typer/Rich/httpx, entry point `mem0 = mem0_cli.app:main`.
- Node package facts from repo metadata: `@mem0/cli` version `0.2.9`, Node `>=18`, ESM binary `dist/index.js`, Commander-based.
- The checked CLI contract is `specVersion: 1`; the CLI spec’s own `cli.version` is `0.1.0`, so do not confuse spec version with package release versions.
- Agent/programmatic output uses a JSON envelope; human output may contain tables, colors, spinners, and status text.

## Read Before Acting

- Command catalog and parity: [references/command-reference.md](references/command-reference.md)
- Config precedence and secrets: [references/configuration.md](references/configuration.md)
- Agent mode, JSON parsing, stdin/files, import/export recipes: [references/agent-json-workflows.md](references/agent-json-workflows.md)
- Failure diagnosis: [references/troubleshooting.md](references/troubleshooting.md)

## Bundled Helpers

- `scripts/summarize_cli_spec.py` summarizes a Mem0 CLI spec JSON into Markdown or JSON without contacting Mem0.
- `scripts/validate_cli_json.py` validates Mem0 CLI agent-mode envelopes, raw JSON outputs, import files, and config snapshots using local JSON only.

## Working Rules

- Never print, log, commit, or paste raw API keys; prefer env vars and redacted config views.
- For automation, prefer `mem0 --agent <command>` or `mem0 <command> --output json` and parse stdout only.
- Put destructive commands behind `--dry-run` first when available, then require explicit `--force` for agent/CI flows.
- Treat CLI flags as highest precedence, then environment variables, then `~/.mem0/config.json`, then built-in defaults.
- If any explicit scope flag is provided (`--user-id`, `--agent-id`, `--app-id`, `--run-id`), do not assume unspecified scope IDs are filled from config defaults.
