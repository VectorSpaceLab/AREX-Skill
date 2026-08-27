---
name: tools-and-agents
description: "Defines, audits, executes, and composes Mellea 0.8.0.dev0 tools
  and ReAct agents with explicit schema, approval, sandbox, hook, MCP, and
  context-compaction boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tools and agents

Use this route when a task exposes a Python callable, shell or Python execution,
MCP/LangChain/smolagents tool, model tool call, ReAct loop, tool hook, or
conversation compaction policy. Treat every model-produced tool request as
untrusted data until its tool name, schema, arguments, side effects, and
execution boundary have been approved.

## Route first

1. Read [the API reference](references/api-reference.md) for exact imports,
   return values, tool-call parsing/validation, execution tiers, and optional
   dependencies.
2. Read [workflows](references/workflows.md) for the smallest suitable recipe:
   plain callable, manual tool loop, ReAct, MCP, framework adapter, or
   compaction.
3. Read [safety and policies](references/safety-and-policies.md) before
   registering an execution-capable, networked, credentialed, or MCP tool.
4. For failures, use [troubleshooting](references/troubleshooting.md). Run the
   bundled static checker before manually approving a serialized request:
   `python scripts/audit_tool_request.py --help`.

## Operating rules

- A tool schema advertises a callable; it is not approval to call it. Prefer
  narrow, typed functions and explicit names. Use `@tool` or
  `MelleaTool.from_callable`; call `.run()` for a deliberate direct call.
- `instruct()`, `act()`, and `aact()` can produce tool calls but do not execute
  them. Use `call_tools()`/`acall_tools()` for an explicit execution boundary.
  `react()` is different: it executes each non-final tool turn itself, so its
  registered tool list is an execution allowlist, not merely context.
- Validate both the request shape and the business policy. Use
  `validate_tool_arguments(..., strict=True)` for schema validation at a manual
  boundary, and `uses_tool`/`tool_arg_validator` when generation must satisfy a
  requirement-and-repair loop. Lenient validation returns original arguments;
  it is not a safety gate.
- Treat local shell and local Python tiers as host execution. Capability policy
  booleans on local tiers are declarations, not isolation. Prefer static checks
  for inspection and Docker-backed execution for untrusted code; still review
  network, package, filesystem, credential, and artifact behavior.
- Discover MCP tools first, inspect/filter their names and schemas, then wrap
  only approved specs. Treat server descriptions, results, headers, stdio
  commands, and environment values as untrusted boundary data.
- Use `tool_pre_invoke` for the final allowlist/argument/redaction decision and
  `tool_post_invoke` for audit or output redaction. Preserve ReAct's internal
  `final_answer` control-flow tool unless the policy intentionally handles
  `is_control_flow`.
- Pin the ReAct initiator before compaction. Keep backend-calling summarizers
  out of per-append `ChatContext` compaction; use a per-turn or thresholded
  compactor instead.

Core generative-program design, session/context generation, and validation
repair belong to [generative-programming](../generative-programming/SKILL.md).
Provider/model selection belongs to `backends-and-models`. Serving, `m`, and
endpoint deployment belong to [serving-and-cli](../serving-and-cli/SKILL.md).
Telemetry and general plugin lifecycle belong to
`observability-and-extensions`; this route owns the tool-execution hook payload
and policy decision.
