---
name: cli-loaders
description: "Guide Swarms CLI commands, YAML configs, markdown agent loaders,
  and autoswarm workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# CLI and loaders

Use this sub-skill when the user is starting from a `swarms` command, a YAML file, or a markdown file.

## Owns these workflows

- Parse and route `swarms` CLI commands.
- Scaffold or validate a project with `setup-check`, `onboarding`, and `init`.
- Create and run agents from YAML with `run-agents`.
- Load agents from markdown frontmatter with `load-markdown`.
- Generate a swarm automatically with `autoswarm`.
- Discover commands, models, and tips with `help`, `features`, `models`, and `tips`.

## Does not own

- The `Agent` class itself; use `single-agent` for runtime behavior and memory.
- Multi-agent orchestration details; use `multi-agent-workflows` for that.
- Tool schema conversion or MCP transport; use `tools-mcp`.

## Read this sub-skill when the request mentions

- `swarms agent`, `swarms run-agents`, `swarms load-markdown`, or `swarms autoswarm`.
- A YAML config, markdown frontmatter, or a command-line parser error.
- `setup-check`, `onboarding`, `init`, `tips`, or `models`.
- A desire to turn a CLI command into a reusable script or smoke check.

## Working shape

1. Start from the command or file format the user already has.
2. Decide whether the task is parser help, file validation, agent creation, or swarm generation.
3. Use the bundled CLI reference for flags and the workflow reference for file layouts.
4. Prefer parser and validation checks before any command that would call a model.

## What to read next

- `references/cli-reference.md` for the verified command and flag catalog.
- `references/workflows.md` for YAML and markdown loader recipes.
- `references/troubleshooting.md` for command, parsing, and missing-argument recovery.
- `scripts/cli_smoke.sh` for an offline parser and loader smoke check.

## Typical user questions this sub-skill should answer

- What flags does `swarms agent` accept?
- How should a YAML config be structured for `run-agents`?
- Why does `load-markdown` reject my file?
- What is the safest way to preview `autoswarm` output without running the swarm immediately?

## Route boundaries

- If the user is asking how the agent behaves after the CLI creates it, route to `single-agent`.
- If the user wants a swarm architecture or router decision, route to `multi-agent-workflows`.
- If the user asks about tool schemas or MCP setup, route to `tools-mcp`.

## Acceptance checklist

- The response should state the exact command or file layout that matters.
- The response should call out required flags and mandatory fields.
- The response should explain how to validate the config before execution.
- The response should distinguish parser errors from live-provider or runtime errors.
