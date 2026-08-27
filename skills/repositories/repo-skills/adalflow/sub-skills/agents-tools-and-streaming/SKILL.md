---
name: agents-tools-and-streaming
description: "Use AdalFlow Agent, Runner, ReActAgent, FunctionTool, ToolManager,
  streaming events, permissions, and MCP tools safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agents, Tools, and Streaming

Use this sub-skill when the task involves AdalFlow agent execution, tool wrapping, tool calling, streaming run events, human approval for tools, or MCP-served tools.

## Route here for

- Wrapping Python callables as `FunctionTool`, including sync, async, sync-generator, async-generator, and bound-method tools.
- Inspecting or constructing `FunctionDefinition`, `Function`, `FunctionExpression`, `FunctionOutput`, or `ToolOutput` values.
- Building a `ToolManager`, parsing function expressions, or executing tool calls directly.
- Constructing `Agent`, `Runner`, or legacy `ReActAgent` workflows after the model client / generator setup is known.
- Calling `Runner.call`, `Runner.acall`, or `Runner.astream` and consuming `RunnerResult`, step history, and stream events.
- Adding human-in-the-loop approvals through `PermissionManager`, CLI/FastAPI handlers, `require_approval`, or pre-execution confirmation details.
- Integrating MCP tools through MCP server parameter dataclasses, `MCPFunctionTool`, and `MCPToolManager`.

## Route elsewhere

- Model client, provider credentials, `Generator`, prompt/model kwargs, and provider streaming setup belong to `model-client-and-generator-workflows`.
- DataClass schemas, parser design, and general structured output repair belong to `core-components-and-structured-io` unless the schema is specifically an agent final `answer_data_type`.
- Retrieval/RAG tools belong to `retrieval-rag-and-data-pipelines` before wrapping them for agent use here.
- Tracing spans, logs, MLflow, and persistent observability belong to `tracing-observability-and-configuration`.
- Training and optimizer behavior for agents/tools belongs to `evaluation-and-optimization`.

## Read these references

1. [references/agents-and-tools.md](references/agents-and-tools.md) for `FunctionTool`, `ToolManager`, `Agent`, `Runner`, `ReActAgent`, tool outputs, and fake-planner testing.
2. [references/streaming-and-run-results.md](references/streaming-and-run-results.md) for `RunnerResult`, `StepOutput`, streaming event types, and robust event consumption loops.
3. [references/mcp-and-permissions.md](references/mcp-and-permissions.md) for tool approval flows, permission handlers, and MCP manager/server parameter patterns.
4. [references/troubleshooting.md](references/troubleshooting.md) for unsafe tools, missing annotations, async-loop issues, result formatting, max-step exhaustion, finalization, permission denials, stream consumption, and missing MCP dependencies.

## Safe bundled checks

- `python scripts/function_tool_smoke.py` verifies service-free `FunctionTool` and `ToolManager` behavior.
- `python scripts/agent_runner_fake_planner_smoke.py` verifies `Agent` + `Runner` sync, async, streaming, and permission behavior with a fake planner and no provider calls.

Run these only in an environment where `adalflow` is importable. They do not require API keys, network services, provider calls, or MCP servers.
