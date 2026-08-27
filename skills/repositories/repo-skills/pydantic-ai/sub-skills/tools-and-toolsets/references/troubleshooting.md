# Tools and Toolsets Troubleshooting

Use this checklist when Pydantic AI tools are not exposed, schemas fail, retries loop, approval/deferred flows stall, or toolsets collide.

## Wrong Decorator or RunContext Shape

Symptoms:

- Schema generation fails for a `RunContext` parameter.
- A context-taking function registered with `tool_plain` behaves like the model must provide `ctx`.
- A plain function registered through `FunctionToolset.tool()` emits a deprecation warning.

Fixes:

- Use `@agent.tool` or `FunctionToolset.tool` when the first parameter is `ctx: RunContext[DepsT]`.
- Use `@agent.tool_plain` or `FunctionToolset.tool_plain` when the function has only model-supplied arguments.
- When using `Tool(...)`, set `takes_ctx=True` or `False` only if inference is ambiguous.
- Keep `Agent(deps_type=...)`, `RunContext[...]`, and the `deps=` value passed to `run` aligned.

## Invalid or Weak JSON Schema

Symptoms:

- Registration raises a schema/user error.
- The provider rejects tool schemas in strict mode.
- The model supplies incorrect nested data repeatedly.

Fixes:

- Replace ambiguous types, untyped params, `*args`, `**kwargs`, or arbitrary objects with Pydantic models, `TypedDict`, enums, literals, lists, dicts with typed values, and primitive scalar types.
- Add concrete return annotations before enabling `include_return_schema=True`.
- Use `Tool.from_schema(...)` only when you already own a reliable JSON schema or must adapt an awkward callable.
- Keep `strict=True` schemas simple and provider-compatible; if a provider rejects a strict schema, first test with `strict=None` or simplify the parameter model.

## Missing Parameter Descriptions

Symptoms:

- `require_parameter_descriptions=True` raises a `UserError`.
- Tool descriptions are present but parameter descriptions are missing.

Fixes:

- Add docstring parameter entries in the selected `docstring_format`.
- Set `docstring_format='google'`, `'numpy'`, or `'sphinx'` when auto-detection guesses wrong.
- Override `description=` for the overall tool description, but still document parameters if parameter descriptions are required.
- On `FunctionToolset`, remember constructor defaults apply to tools unless each decorator overrides them.

## Unsupported or Misleading Return Values

Symptoms:

- Return schemas are missing even though return schemas were requested.
- A tool returns content the model or app cannot serialize cleanly.
- App-only metadata is accidentally expected to appear in the model transcript.

Fixes:

- Return JSON-serializable values, Pydantic models, or typed containers.
- Use `ToolReturn(return_value=..., content=..., metadata=...)` to separate model-facing value, extra user content, and app-only metadata.
- Parameterize `ToolReturn[T]` if you need a return schema; a bare `ToolReturn` produces no constrained schema.
- Do not rely on `metadata` fields being sent to the model. They are for application/toolset logic.

## ModelRetry Loops

Symptoms:

- The run raises `UnexpectedModelBehavior` because a tool exceeded its retry count.
- The model repeats invalid calls after validation or `ModelRetry` prompts.
- A timeout appears as a retry prompt.

Fixes:

- Make `ModelRetry` messages specific and actionable: name the invalid argument, valid range, and correction.
- Check retry precedence: per-tool `retries`, `FunctionToolset(max_retries=...)`, then `Agent(retries={'tools': ...})`.
- Inspect `ctx.retry`, `ctx.max_retries`, and `ctx.last_attempt` for fallback behavior inside a tool.
- Use `args_validator` for argument business rules so approval is not requested before the model can fix invalid args.
- Avoid side effects before validation and approval checks; retries can call the same tool again.

## Approval and Deferred Result Mismatch

Symptoms:

- `DeferredToolRequests.build_results(...)` raises about unknown IDs.
- A deferred external call is resumed through `approvals`, or an approval is resumed through `calls`.
- A tool still raises `ApprovalRequired` after approval.

Fixes:

- Preserve exact `tool_call_id` values from `DeferredToolRequests.approvals` and `.calls`.
- Put approval decisions in `DeferredToolResults(approvals={...})` and external execution results in `DeferredToolResults(calls={...})`.
- Include `DeferredToolRequests` in `output_type` unless a deferred-call handling capability resolves every request inline.
- Resume with the prior `message_history` plus `deferred_tool_results`.
- Inside tools that raise `ApprovalRequired` conditionally, check `ctx.tool_call_approved` before raising again.
- Use `ToolApproved(override_args=...)` only when changing args is intentional; otherwise approve with `True` or `ToolApproved()`.

## Tool Name Collisions

Symptoms:

- Combining toolsets raises a conflict error.
- A function tool conflicts with an output tool.
- A prefixed tool still conflicts after composition.

Fixes:

- Give tools stable unique names with `name=` when registering.
- Wrap independent catalogs with `.prefixed('domain')` before `CombinedToolset`.
- Use `.renamed({'new_name': 'old_name'})` for targeted renames.
- Avoid generic names such as `search`, `lookup`, or `run` in shared catalogs unless they are prefixed.
- Remember `PrefixedToolset` exposes `prefix_original` to the model while internally calling the original tool name.

## Too Many Tools Without Search

Symptoms:

- Prompts become large or slow because every tool schema is sent.
- Important tools are ignored among many similar names.
- Provider prompt caching becomes ineffective after large tool changes.

Fixes:

- Mark low-frequency tools with `defer_loading=True` or wrap catalogs with `.defer_loading()`.
- Add `ToolSearch` when strategy control is needed; leave the default when provider portability matters.
- Improve names, descriptions, and parameter descriptions before hiding tools behind search.
- Keep high-frequency tools visible and defer rare or bulky catalogs.
- Route on-demand capabilities and integration-heavy search behavior to `../../mcp-and-integrations/SKILL.md` when capability lifecycle is the main task.

## PreparedToolset Pitfalls

Symptoms:

- `PreparedToolset` raises that prepare functions cannot add or rename tools.
- Returning `None` from a prepare callback produces warnings or hides every tool unexpectedly.

Fixes:

- Use `FunctionToolset.add_function()` to add tools.
- Use `RenamedToolset` or `PrefixedToolset` to rename tools.
- Use `PreparedToolset` only to remove existing tools or replace existing `ToolDefinition` values by the same name.
- Return a list of tool definitions. Avoid returning `None`; use an empty list when no tools should be exposed.

## Native Provider and MCP Boundaries

- If a task asks for provider-native tools such as web search, code execution, file search, memory, or native MCP tool calls, route to `../../models-and-providers/SKILL.md`.
- If a task asks for MCP client/server transport, FastMCP, server lifecycle, or agent-as-MCP-server patterns, route to `../../mcp-and-integrations/SKILL.md`.
- If a task asks about final result tools, structured output, output function retries, or message history serialization, route to `../../outputs-and-messages/SKILL.md`.
