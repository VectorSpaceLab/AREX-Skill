---
name: tools-and-toolsets
description: "Guides agents that define, validate, organize, approve, defer,
  search, retry, and compose Pydantic AI function tools and toolsets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Tools and Toolsets

Use this sub-skill when a task involves Pydantic AI function tools, tool decorators, tool schemas, `RunContext`, `ModelRetry`, tool approvals, deferred calls, tool search, or `FunctionToolset` composition.

## Routing

- Read [references/tool-api.md](references/tool-api.md) to choose between `@agent.tool`, `@agent.tool_plain`, `Tool`, `Tool.from_schema`, `ToolReturn`, validators, prepare callbacks, return schemas, and retry/timeout knobs.
- Read [references/toolset-workflows.md](references/toolset-workflows.md) when organizing many functions into `FunctionToolset`, composing wrappers, prefixing/filtering/preparing tools, requiring approvals, deferring loading, or exposing external tool definitions.
- Read [references/troubleshooting.md](references/troubleshooting.md) when schema generation, docstring extraction, approval/deferred flows, retries, tool names, or large tool collections behave unexpectedly.
- Run [scripts/tool_schema_smoke.py](scripts/tool_schema_smoke.py) after installing `pydantic-ai` to verify local imports, schema extraction, `TestModel` request parameters, prefix/filter/prepare wrappers, and return-schema exposure without network access.

## Decision Guide

- Use individual `@agent.tool` or `@agent.tool_plain` decorators for a small set of agent-specific tools that belong only to one `Agent`.
- Use `Tool(...)` or `Tool.from_schema(...)` when functions are registered through `Agent(tools=[...])`, schema control is explicit, or a callable comes from another layer.
- Use `FunctionToolset` when a reusable group of local Python functions needs shared instructions, default retries, default schema settings, approval policy, metadata, or durable `id` values.
- Use wrapper toolsets when behavior changes by run context: `PrefixedToolset` for name collisions, `FilteredToolset` for access control, `PreparedToolset` for per-step definition edits, `ApprovalRequiredToolset` for human approval gates, `.defer_loading()` with `ToolSearch` for large tool catalogs, and `ExternalToolset` for frontend/upstream execution.
- Route final-output function design and output tools to `../outputs-and-messages/SKILL.md`, model/provider native tools to `../models-and-providers/SKILL.md`, MCP/FastMCP transports to `../mcp-and-integrations/SKILL.md`, and agent construction/run-context basics to `../agent-core/SKILL.md`.

## Safety Defaults

- Prefer deterministic `TestModel` or `FunctionModel` checks before live provider runs.
- Keep tool bodies idempotent where possible; use `requires_approval=True`, `ApprovalRequired`, `ExternalToolset`, or `CallDeferred` before expensive, destructive, or user-visible actions.
- Validate model-supplied arguments with type hints first, then add `args_validator` for business rules that should produce `ModelRetry` instead of a terminal exception.
- Prefix or rename toolsets before combining independent catalogs, and enable tool search only after important tools have clear names and descriptions.
