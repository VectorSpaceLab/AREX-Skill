# Troubleshooting: Agents, Tools, and HITL

Use this guide when agent/tool behavior fails at import time, schema generation, execution, state updates, HITL confirmation, connector setup, or debugging/resume.

## Install and Import Failures

Symptoms:

- `ModuleNotFoundError: No module named 'haystack'`
- imports work for `haystack` but fail for MCP, OpenAPI helper packages, `rich`, or provider generators
- examples import `haystack_experimental` but the current task uses core `haystack-ai`

Fixes:

- Install the public package as `haystack-ai`; import the package as `haystack`.
- Use core imports for this sub-skill: `haystack.components.agents`, `haystack.components.tools`, `haystack.tools`, and `haystack.human_in_the_loop`.
- Optional UI `RichConsoleUI` requires `rich`; use `SimpleConsoleUI` if optional dependencies are unavailable.
- MCP tools usually come from integration packages such as `haystack_integrations.tools.mcp`; do not assume they are present in a minimal `haystack-ai` install.
- Provider chat generators and credentials are covered by `../generation-and-model-components/SKILL.md`.

## Chat Generator Does Not Support Tools

Symptoms:

- `Agent(...)` raises `TypeError` about `chat_generator` not supporting a `tools` parameter.
- The model returns plain text instead of tool calls.
- Runtime `tools` passed to the generator are ignored.

Fixes:

- Inspect the generator API and choose a chat generator with tool-calling support.
- Pass Haystack `Tool`/`Toolset` objects, not raw OpenAI/MCP tool definitions mixed with Haystack tools unless that provider explicitly supports it.
- Keep tool names valid for the provider: short, unique, snake_case names are safest.
- Provide precise descriptions and parameter descriptions; vague tool specs reduce tool-call likelihood.

## Tool Schema Generation Fails

Symptoms:

- `ValueError: parameter ... does not have a type hint`
- `SchemaGenerationError`
- invalid JSON Schema errors from `Tool(...)`
- enum or parameter descriptions missing from `tool.tool_spec`

Fixes:

- Add type hints to every LLM-visible function parameter.
- Use `Annotated[type, "description"]` for parameter descriptions.
- Use `Literal[...]` for enum-like choices.
- Map hidden parameters with `inputs_from_state` or type a parameter as `State` if it should be injected at runtime.
- Avoid arbitrary custom classes in function-tool signatures; use dict/list/dataclass-friendly values or write manual JSON Schema.
- For manual `Tool(...)`, validate the `parameters` dict as JSON Schema before passing it to a generator.

Run the bundled smoke script from this sub-skill directory:

```bash
python scripts/tool_schema_smoke_check.py
```

## Async Tool Function Rejected

Symptoms:

- `ValueError: Async functions are not supported as tools`

Fixes:

- Wrap async backend calls in a synchronous boundary before creating a `Tool`, or implement the async behavior inside a component/pipeline and expose a supported synchronous interface.
- If the whole application is async, use `Agent.run_async` for orchestration but keep individual `Tool` functions synchronous unless a specific integration documents otherwise.

## Duplicate or Missing Tools

Symptoms:

- duplicate-name validation errors in `Toolset`, `ToolInvoker`, or `Agent`
- `Tool 'x' not found. Available tools: ...`
- a `SearchableToolset` agent only sees `search_tools`

Fixes:

- Give every tool a unique name before grouping.
- Use `Toolset([tool])`, not `Toolset(tool)`.
- For runtime `Agent.run(..., tools=...)`, remember that tool names select from the agent's configured catalog; unknown names are invalid.
- With `SearchableToolset`, instruct the model to call the bootstrap search tool first using keywords from tool names/descriptions, not the full user question.
- Call `SearchableToolset.clear()` between unrelated runs if discovered tools from prior runs should not remain available.

## Tool Invocation Fails

Symptoms:

- `ToolInvocationError`
- missing required positional arguments
- tool result conversion errors
- `ToolInvoker` raises instead of returning an error message

Fixes:

- Compare `ToolCall.arguments` with `tool.tool_spec["parameters"]`.
- Test `tool.invoke(...)` directly before using an LLM.
- Set `ToolInvoker(raise_on_failure=False)` or `Agent(..., raise_on_tool_invocation_failure=False)` if the model should see and recover from errors.
- Use `convert_result_to_json_string=True` if downstream parsing expects JSON strings.
- For structured outputs, configure `outputs_to_string` so the LLM sees a concise value instead of a huge dict.
- Avoid non-serializable return values unless using `raw_result=True` for supported multimodal content.

## State Mapping Fails

Symptoms:

- state value not available to a tool
- `inputs_from_state` references unknown parameter
- `outputs_to_state` references unknown output for `ComponentTool`/`PipelineTool`
- accumulated state is overwritten or cannot be serialized

Fixes:

- Define the key in `Agent(state_schema=...)` with the intended type.
- Ensure `inputs_from_state={"state_key": "tool_parameter"}` uses an actual function parameter or component input socket.
- For component/pipeline tools, ensure `outputs_to_state` source names match output sockets or mapped output names.
- Add merge handlers for accumulated list/dict state when needed.
- Keep state values serializable if snapshots or pipeline serialization are needed.

## ComponentTool Problems

Symptoms:

- `Object ... is not a Haystack component`
- `Component has been added to a pipeline and can't be used to create a ComponentTool`
- schema contains internal or confusing socket names
- output mapping errors

Fixes:

- Decorate custom classes with `@component` and add `@component.output_types` to `run`.
- Instantiate a fresh component for `ComponentTool`; do not reuse one already added to a `Pipeline`.
- Override `name`, `description`, or `parameters` if the generated schema is not LLM-friendly.
- Use `outputs_to_string` and `outputs_to_state` with valid output socket names.

## PipelineTool Problems

Symptoms:

- `pipeline` argument type error
- LLM sees too many or unclear parameters
- pipeline outputs are too verbose for tool messages
- async pipeline serialization/resume confusion

Fixes:

- Pass a `Pipeline` or `AsyncPipeline` instance.
- Use explicit `input_mapping` to expose stable parameters such as `query`, not internal socket paths.
- Use explicit `output_mapping` and `outputs_to_string` to surface only the result needed by the agent.
- If the tool wraps retrieval or RAG internals, route deep retrieval debugging to `../retrieval-and-rag/SKILL.md`.
- For base pipeline construction or connection errors, route to `../pipelines-and-components/SKILL.md`.

## HITL Confirmation Fails

Symptoms:

- confirmation UI never appears
- strategy applies to wrong tool or not at all
- multiple tool calls get the wrong decision
- `RichConsoleUI` import prompts for installing `rich`
- a web app blocks waiting for console input

Fixes:

- Confirm `confirmation_strategies` keys exactly match tool names; use tuple keys for shared strategies.
- Use `AlwaysAskPolicy` while debugging, then narrow to `AskOncePolicy` or a custom policy.
- Preserve `tool_call_id` in custom strategies when an assistant message can contain multiple calls.
- Use `SimpleConsoleUI` when `rich` is unavailable.
- Do not use blocking console UIs in web/server request handlers; implement a custom `ConfirmationStrategy` using `confirmation_strategy_context` for queues, WebSockets, or pub/sub.
- Handle all UI actions: `confirm`, `reject`, and `modify`.

## Agent Loops or Stops Incorrectly

Symptoms:

- agent repeatedly calls the same tool
- agent stops before using a needed tool
- agent exceeds `max_agent_steps`
- agent returns a tool message instead of final answer

Fixes:

- Tighten system prompt instructions about when to use each tool and when to answer.
- Set `exit_conditions=["text"]` for normal answer-on-text behavior, or include a tool name only if tool execution itself should end the run.
- Lower `max_agent_steps` in production and inspect `result["messages"]` to find the loop cause.
- Improve tool output strings so the model can tell whether the tool succeeded.
- If using `SearchableToolset`, ensure the bootstrap search result tells the model the discovered tool names are now available.
- Check HITL rejection/modify feedback; vague rejection messages can cause repeated attempts.

## Breakpoint and Snapshot Issues

Symptoms:

- breakpoint never triggers
- snapshot files are not written
- resume starts at the wrong point
- snapshots contain sensitive data

Fixes:

- Use component names `chat_generator` or `tool_invoker` for agent internals.
- For tool breakpoints, set `ToolBreakpoint(component_name="tool_invoker", tool_name="exact_tool_name")`.
- Snapshot file saving is disabled by default; use `snapshot_callback` for programmatic handling or intentionally enable file saving with `HAYSTACK_PIPELINE_SNAPSHOT_SAVE_ENABLED`.
- When an agent is inside a pipeline, resume via `pipeline.run(data={}, pipeline_snapshot=snapshot)`.
- Review snapshot content before persisting; tool arguments and state may contain secrets or personal data.

## Optional Connector and Backend Failures

Symptoms:

- MCP/OpenAPI imports fail
- external tool catalog is huge or unreliable
- credentials missing for a connector or provider
- external write operation executes without review

Fixes:

- Verify the installed integration package and current import path before writing code.
- Restrict MCP/OpenAPI tool names with allowlists whenever available.
- Wrap large connector catalogs in `SearchableToolset`.
- Add HITL for side-effecting operations such as writes, sends, purchases, deletes, or ticket creation.
- Keep credentials outside tool descriptions, serialized pipeline definitions, and snapshots.
- Start with dry-run or read-only operations before enabling write tools.

## Quick Diagnostic Sequence

1. Run `tool_schema_smoke_check.py` to prove core tool creation and invocation work.
2. Print each `tool.tool_spec` and check names, descriptions, `required`, and enum values.
3. Invoke each tool directly with valid and invalid parameters.
4. Run `ToolInvoker` with a manually constructed `ToolCall`.
5. Run `Agent` with one simple tool and `max_agent_steps=3`.
6. Add state, `SearchableToolset`, HITL, and external connectors one layer at a time.
