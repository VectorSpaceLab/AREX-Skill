---
name: cli-cloud-operations
description: "Operate mcp-agent projects with mcp-agent, mcp-cloud, and mcpc
  CLIs for scaffolding, diagnostics, local dev, deployment, logs, secrets, and
  client install."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Cloud Operations

Use this sub-skill when a task asks for `mcp-agent`, `mcp-cloud`, or `mcpc` command usage: project scaffolding, config inspection, local dev runs, one-shot invoke/chat/serve, Cloud login/deploy/manage/logs/env/workflows, or installing a deployed server into a local MCP client.

## Start Here

1. Read `references/cli-reference.md` for the command map, safe read-only/help commands, local dev commands, output formats, and non-interactive usage.
2. Read `references/cloud-deployment.md` before deploying, configuring Cloud apps, managing environment secrets, tailing logs, or installing clients.
3. Read `references/troubleshooting.md` when config discovery, schema validation, auth, deployment prompts, ignore files, log filters, or client overwrite behavior is confusing.
4. Use bundled scripts for safe checks:
   - `python scripts/collect_cli_help.py --help`
   - `python scripts/collect_cli_help.py --base-command mcp-agent --commands init deploy "cloud servers list"`
   - `python scripts/check_project_config.py --project . --json`

## Safe Operating Defaults

- Prefer `mcp-agent --help`, subcommand `--help`, `mcp-agent config check`, `mcp-agent config show --raw`, `mcp-agent doctor`, and `mcp-agent dev build --check-only` before mutating local files or Cloud state.
- Set `MCP_AGENT_DISABLE_VERSION_CHECK=1` in CI or scripted help collection to avoid best-effort PyPI version-check noise.
- Use `--format json` or `--format yaml` on list/describe/status commands when another agent or CI job must parse output.
- Use `--non-interactive` on deployment so CI fails instead of prompting. Provide `--config-dir`, `--working-dir`, `--ignore-file`, `--api-key` or `MCP_API_KEY`, and explicit auth flags when policy matters.
- Use `mcp-agent install ... --dry-run` for client configuration previews. Only add `--force` after confirming the target client entry may be overwritten.

## Common Workflows

- **Scaffold:** `mcp-agent init --list`, then `mcp-agent init --template basic --dir app`, or `mcp-agent init --quickstart hello-world --dir cloud-demo --force`.
- **Diagnose config:** run `mcp-agent config check`, `mcp-agent doctor`, and this skill's `scripts/check_project_config.py --project app --json` to confirm which config and secrets files are discovered.
- **Local dev:** run `mcp-agent dev start --script main.py`, `mcp-agent dev chat --message "ping"`, `mcp-agent dev invoke --agent researcher --message "..."`, or `mcp-agent dev serve --transport stdio --show-tools`.
- **Deploy:** run config checks first, then `mcp-agent deploy APP_NAME --config-dir app --working-dir . --ignore-file .mcpacignore --non-interactive --no-git-tag`.
- **Operate Cloud:** use `mcp-agent cloud auth whoami`, `mcp-agent cloud servers list --format json`, `mcp-agent cloud logger tail SERVER --since 1h --grep "ERROR|WARN"`, and `mcp-agent cloud env list APP`.
- **Install client:** preview with `mcp-agent install SERVER_URL --client claude_code --name app-name --dry-run`; write only after reviewing the target client and overwrite policy.

## Route Elsewhere

- Use `../core-sdk/SKILL.md` for Python SDK design, `MCPApp`, `Agent`, `Settings`, LLM factories, secrets schema, and app code structure.
- Use `../mcp-server-integration/SKILL.md` for MCP server/client concepts, transport semantics, `create_mcp_server_for_app`, OAuth primitives, and server internals.
- Use `../workflow-patterns/SKILL.md` for routers, orchestrators, parallel workflows, evaluator loops, and in-process workflow code.
- Use `../durable-execution/SKILL.md` for Temporal worker/runtime design when available in the skill tree.

## Safety Notes

- Cloud deployment, app updates/deletes, env add/remove, workflow resume/suspend/cancel, and client install writes are mutating operations. Confirm credentials, target app/server, and flags before running them.
- The current deploy command is not a read-only dry run. Validate with config/help/build checks first, then deploy only when mutation is intended.
- Do not paste real API keys into command transcripts. Prefer environment variables or secret files and redact generated client snippets before sharing.
