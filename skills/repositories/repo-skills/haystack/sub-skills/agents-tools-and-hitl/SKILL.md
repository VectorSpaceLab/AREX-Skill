---
name: agents-tools-and-hitl
description: "Build Haystack agents and tool ecosystems with Tool, Toolset,
  ComponentTool, PipelineTool, ToolInvoker, optional MCP/OpenAPI connectors,
  state, breakpoints, snapshots, and human-in-the-loop confirmation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Agents, Tools, and HITL

Use this sub-skill when a task asks for Haystack `Agent` loops, tool definitions, tool catalogs, tool execution, external tool connectors, human approval before tool execution, or agent debugging with tool breakpoints and snapshots.

## Route Here For

- Creating `Tool` objects from Python functions with `@tool`, `create_tool_from_function`, or explicit JSON schema.
- Passing `Tool`, `Toolset`, `SearchableToolset`, `ComponentTool`, or `PipelineTool` to an `Agent`, chat generator, or `ToolInvoker`.
- Wrapping Haystack components, pipelines, OpenAPI operations, or MCP tools for LLM tool calling.
- Configuring `Agent` state via `state_schema`, `inputs_from_state`, `outputs_to_state`, and `outputs_to_string`.
- Adding HITL confirmation with `BlockingConfirmationStrategy`, policies, console UIs, or custom async strategies.
- Debugging tool calls with `ToolInvoker`, `AgentBreakpoint`, `ToolBreakpoint`, snapshots, and resume flows.

## Reroute

- Base component decoration, socket wiring, pipeline serialization, or pipeline execution mechanics: `../pipelines-and-components/SKILL.md`.
- Chat generator/provider credential setup and model-specific tool support: `../generation-and-model-components/SKILL.md`.
- Retriever behavior, document stores, ranking, embedding, and RAG internals: `../retrieval-and-rag/SKILL.md`.

## Fast Path

1. Choose the orchestration level:
   - `Agent` for the full loop: chat generator -> tool call -> tool execution -> state update -> next message.
   - `ToolInvoker` when the application already controls chat-generator calls and only needs to execute prepared `ToolCall`s.
2. Define tool schemas from typed functions whenever possible. Use `Annotated[..., "description"]`, `Literal[...]`, and docstrings so LLM-visible schemas are useful.
3. Keep tool names unique and action-oriented. Duplicate names raise validation errors in `Toolset`, `ToolInvoker`, and agent setup.
4. Use `ComponentTool` for one Haystack component and `PipelineTool` for a whole pipeline. Create tools from non-pipeline component instances; components already added to a pipeline cannot be wrapped by `ComponentTool`.
5. Use `state_schema` on `Agent` plus `inputs_from_state` and `outputs_to_state` on tools when tool calls need shared memory.
6. Add HITL only around risky tools, using `confirmation_strategies={"tool_name": strategy}` or tuple keys for shared strategies.
7. Validate offline with `scripts/tool_schema_smoke_check.py` before adding provider-specific chat generators.

## Reference Map

- `references/api-reference.md`: public imports, constructors, parameters, return shapes, state, HITL, connectors, and breakpoints.
- `references/workflows.md`: implementation recipes for function tools, component/pipeline tools, manual invocation, HITL, external tools, state, and debugging.
- `references/troubleshooting.md`: import/install, optional dependency, credential/backend, schema, state, ToolInvoker, HITL, snapshot, and connector failure modes.
- `scripts/tool_schema_smoke_check.py`: deterministic offline check for function schema generation, `Toolset`, `ToolInvoker`, and state input/output mappings.

## Safety Defaults

- Do not run arbitrary shell/network tools from an agent without HITL or explicit allowlisting.
- Prefer `SearchableToolset` for large catalogs so the model does not see dozens of irrelevant tools at once.
- For external MCP/OpenAPI tools, filter exposed tool names and validate operation schemas before enabling automatic execution.
- For user-facing systems, set conservative `max_agent_steps`, meaningful `exit_conditions`, and `raise_on_tool_invocation_failure=False` when the model should recover from tool errors.
