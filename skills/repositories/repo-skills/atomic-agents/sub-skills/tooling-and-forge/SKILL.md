---
name: tooling-and-forge
description: "Use BaseTool, BaseResource, BasePrompt, Atomic Forge tool
  packages, the atomic CLI, and tool-selection patterns safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tooling and Forge

Use this subskill when a task is about Atomic Agents tool abstractions, Atomic Forge downloadable tools, the `atomic` CLI/TUI, or choosing between direct tool calls and LLM-selected tool routing.

## Read first

- `references/api-reference.md` for `BaseTool`, `BaseResource`, `BasePrompt`, and tool composition patterns.
- `references/cli-reference.md` for the `atomic` command and Atomic Assembler behavior.
- `references/forge-catalog.md` for the downloadable tool families and their dependency / credential notes.
- `references/troubleshooting.md` for CLI, download, dependency, and selection failures.
- `../../scripts/check_atomic_agents_env.py` from the root skill for a safe CLI/import smoke check.

## Owns

- `BaseTool`, `BaseToolConfig`, `BaseResource`, `BaseResourceConfig`, `BasePrompt`, and `BasePromptConfig`.
- Direct tool calls versus choice-agent orchestration patterns.
- Atomic Forge tool selection, download expectations, and dependency/credential caveats.
- Atomic Assembler / `atomic` CLI usage and common local setup mistakes.
- Tool authoring guidance when a task is about packaging a reusable tool.

## Does not own

- Core agent construction, history, prompts, hooks, or token counting; use `../agent-core/SKILL.md`.
- MCP transport and dynamic tool discovery; use `../mcp-integrations/SKILL.md`.
- Example project adaptation; use `../example-workflows/SKILL.md`.
- Repo editing / docs / release / CI; use `../repo-development/SKILL.md`.

## Common triggers

- "How do I create a tool?"
- "How do I use Atomic Forge tools?"
- "What does the `atomic` CLI download?"
- "How should I choose between a direct tool call and an LLM-selected tool?"
- "What dependencies or API keys does this tool family need?"
