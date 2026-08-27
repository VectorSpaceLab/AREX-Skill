---
name: agents-tasks-tools
description: "Build and debug Langroid ChatAgent, Task, and ToolMessage
  workflows, including routing, orchestration tools, done sequences, structured
  output, batch helpers, XML tools, and MockLM tests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Agents, Tasks, and Tools

Use this sub-skill for Langroid work centered on:

- `ChatAgentConfig` and `ChatAgent`
- `TaskConfig` and `Task`
- `ToolMessage` and `XMLToolMessage`
- orchestration tools such as `DoneTool`, `ResultTool`, and `FinalResultTool`
- `TaskTool` and `RecipientTool`
- `done_sequences`, `handle_llm_no_tool`, structured output, batch helpers, and `MockLM`

Use it when the problem is about agent orchestration, tool wiring, routing, termination, typed output, or deterministic testing. If the issue is about provider endpoints, keys, or model backends, route elsewhere first.

## Route elsewhere

- Provider endpoints, keys, or model wiring → [llm-provider-config](../llm-provider-config/SKILL.md)
- RAG, document chat, or retrieval flows → [retrieval-doc-chat](../retrieval-doc-chat/SKILL.md)
- SQL, table, or graph workflows → [data-sql-graph-agents](../data-sql-graph-agents/SKILL.md)
- MCP or Chainlit integrations → [integrations-mcp-chainlit](../integrations-mcp-chainlit/SKILL.md)

## Core pattern

1. Pick the right `ToolMessage` or output type.
2. Enable it with `enable_message`.
3. Add a `ChatAgent` handler or tool-level `handle` / `response` method.
4. Wrap the agent in a `Task`.
5. Add routing or termination only when needed.
6. Test the flow with `MockLM` before using a provider-backed model.

## Read next

- [API reference](references/api-reference.md)
- [Workflows](references/workflows.md)
- [Testing patterns](references/testing-patterns.md)
- [Troubleshooting](references/troubleshooting.md)
