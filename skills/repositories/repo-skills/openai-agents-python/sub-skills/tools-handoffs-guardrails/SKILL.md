---
name: tools-handoffs-guardrails
description: "Build function tools, local and hosted tool surfaces,
  agents-as-tools, handoffs, approvals, and guardrails in openai-agents-python."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tools, Handoffs, and Guardrails

Use this sub-skill when a task mentions `@function_tool`, function schemas, hosted or local tools, `ShellTool`, `ComputerTool`, `ApplyPatchTool`, agents-as-tools, handoffs, human approval, input/output guardrails, or tool guardrails.

## Start Here

- Read [references/api-reference.md](references/api-reference.md) for current constructor/decorator options, selection tables, and API boundaries.
- Read [references/workflows.md](references/workflows.md) for copyable patterns: basic function tools, approval flow, agents-as-tools versus handoffs, deferred tool search, shell/apply-patch/computer tools, and guardrails.
- Read [references/troubleshooting.md](references/troubleshooting.md) when schema generation, strict mode, approvals, guardrail timing, tool lookup, hosted/local execution, or `ComputerTool` model migration is surprising.
- Run [scripts/validate_function_tool_schema.py](scripts/validate_function_tool_schema.py) to inspect safe local `@function_tool` schema behavior without model or API calls.

## Routing Boundaries

- Use this sub-skill for Python function tools, SDK built-in tool classes, `Agent.as_tool()`, `handoff(...)`, `ToolExecutionConfig`, HITL approval pauses, and agent/tool guardrails.
- Route MCP server lifecycle, local MCP configuration, and hosted MCP depth to [../mcp-and-hosted-tools/SKILL.md](../mcp-and-hosted-tools/SKILL.md); keep only high-level hosted tool selection here.
- Route model/provider setup, Responses versus Chat Completions compatibility, and `OpenAIProvider` choices to [../models-providers/SKILL.md](../models-providers/SKILL.md).
- Route sandbox agents, manifests, Docker/hosted sandbox clients, and sandbox capability wiring to [../sandbox-agents/SKILL.md](../sandbox-agents/SKILL.md).
- Route runner lifecycle, sessions, server-managed conversations, streaming, and `RunState` persistence details to [../core-runtime/SKILL.md](../core-runtime/SKILL.md).

## Working Rules

- Prefer `@function_tool` for ordinary Python functions; use explicit `FunctionTool` only when you need a custom raw JSON invoker or manually built schema.
- Keep `strict_mode=True` unless you have verified the target model/provider accepts the looser schema and you have a fallback for validation errors.
- Use `Agent.as_tool()` when a manager should keep conversation control; use `handoff(...)` when a specialist should become the active agent.
- Use tool guardrails for checks around every custom function-tool call; agent input guardrails only cover the first agent input, and agent output guardrails only cover the final-producing agent.
- Treat approval-gated tools as resumable interruptions: inspect `result.interruptions`, convert to `RunState`, approve/reject, then resume the original top-level run.

## Evidence Base

This sub-skill distills the repository docs, source, examples, and tests for tools, handoffs, HITL approvals, guardrails, `ToolExecutionConfig`, deferred tool search, and local/hosted runtime tools. It intentionally bundles patterns instead of linking to original examples so future agents do not depend on a source checkout.
