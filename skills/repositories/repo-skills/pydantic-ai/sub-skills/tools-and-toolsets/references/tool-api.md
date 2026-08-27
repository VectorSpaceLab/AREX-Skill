# Tool API Reference

This reference summarizes verified Pydantic AI function-tool APIs for future agents. For agent construction and run methods, route to `../../agent-core/SKILL.md`.

## Registration Choices

| Use case | API | Notes |
| --- | --- | --- |
| Tool needs dependencies, messages, retry state, approval metadata, or run step | `@agent.tool` / `FunctionToolset.tool` | The function must accept `RunContext[DepsT]` as the first parameter. Use `ctx.deps`, `ctx.retry`, `ctx.max_retries`, `ctx.last_attempt`, `ctx.messages`, `ctx.tool_call_id`, `ctx.tool_call_approved`, and `ctx.tool_call_metadata` as needed. |
| Tool is a pure function of model-supplied args | `@agent.tool_plain` / `FunctionToolset.tool_plain` | The function must not take `RunContext`. Using `@agent.tool_plain` on a context-taking function raises a schema error. |
| Tools are passed through `Agent(tools=[...])` | Plain functions or `Tool(...)` | Pydantic AI infers whether the first parameter is `RunContext` unless `Tool(takes_ctx=...)` is set explicitly. |
| Existing callable has poor annotations or external schema | `Tool.from_schema(...)` | Provide `name`, `description`, JSON schema, and `takes_ctx`. Schema validation is skipped for the callable, but `args_validator` still runs. |
| Many related local functions need shared policy | `FunctionToolset` | Use constructor defaults for retries, timeout, schema/docstring settings, approval, metadata, deferred loading, return schemas, and instructions. |

## Verified Signatures

The inspected checkout exposes these public signatures:

```python
Agent.tool(
    func=None, /, *, name=None, description=None, retries=None, prepare=None,
    args_validator=None, docstring_format='auto', require_parameter_descriptions=False,
    schema_generator=GenerateToolJsonSchema, strict=None, sequential=False,
    requires_approval=False, metadata=None, timeout=None, defer_loading=False,
    include_return_schema=None,
)

Agent.tool_plain(
    func=None, /, *, name=None, description=None, retries=None, prepare=None,
    args_validator=None, docstring_format='auto', require_parameter_descriptions=False,
    schema_generator=GenerateToolJsonSchema, strict=None, sequential=False,
    requires_approval=False, metadata=None, timeout=None, defer_loading=False,
    include_return_schema=None,
)

Tool(
    function, *, takes_ctx=None, max_retries=None, name=None, description=None,
    prepare=None, args_validator=None, docstring_format='auto',
    require_parameter_descriptions=False, schema_generator=GenerateToolJsonSchema,
    strict=None, sequential=False, requires_approval=False, metadata=None,
    timeout=None, defer_loading=False, include_return_schema=None,
    function_schema=None,
)
```

`FunctionToolset.tool`, `FunctionToolset.tool_plain`, and `FunctionToolset.add_function` accept the same per-tool choices, but many default to the toolset constructor when passed as `None`.

## Schema and Description Rules

- Tool parameters come from the Python signature; all parameters except the leading `RunContext` become tool-call arguments.
- Descriptions come from the function docstring unless `description=` is supplied.
- Supported docstring formats are `'auto'`, `'google'`, `'numpy'`, and `'sphinx'`.
- Set `require_parameter_descriptions=True` when missing parameter descriptions should fail fast during registration.
- Use precise Pydantic-compatible annotations. Complex unsupported argument types can fail JSON schema generation; prefer `BaseModel`, `TypedDict`, enums, literals, lists, and primitive scalar types.
- `strict=True` asks compatible providers to enforce strict JSON schema behavior. Keep schemas simple when enabling strict mode.
- `metadata` is not sent to the model; it is for filtering, selectors, wrapper behavior, or app-side bookkeeping.

## Validation and Retry

- Type validation runs before tool execution. Validation failures produce retry prompts and count against the tool retry budget.
- `args_validator(ctx, **validated_args)` runs after schema validation and before approval/execution. It can be sync or async, should return `None` on success, and should raise `ModelRetry(message)` for fixable argument problems.
- A tool body can raise `ModelRetry(message)` for recoverable execution failures that the model can fix with a new call.
- Retry precedence is per-tool `retries=` or `Tool(max_retries=...)`, then `FunctionToolset(max_retries=...)`, then `Agent(retries={'tools': ...})`, then the default.
- Tool retries are per tool, not a global call budget. When exhausted, the run raises `UnexpectedModelBehavior` with a message that the tool exceeded its max retries count.
- `timeout=` creates a retry prompt when execution exceeds the per-tool or inherited timeout.

## Prepare Functions

Use `prepare(ctx, tool_def)` for per-step tool-definition changes or conditional registration.

```python
from dataclasses import replace
from pydantic_ai import RunContext, ToolDefinition


def only_for_admin(ctx: RunContext[str], tool_def: ToolDefinition) -> ToolDefinition | None:
    if ctx.deps != 'admin':
        return None
    return replace(tool_def, description=f'{tool_def.description} Admin only.')
```

- Returning `None` omits that tool for the step.
- Return a replaced `ToolDefinition` to edit description, schema flags, metadata, timeout, or deferred state.
- Use `PreparedToolset` for whole-toolset edits; do not use it to add or rename tools.

## Return Values

- Most JSON-serializable Python values, Pydantic models, and typed containers can be returned from tools and sent back to the model.
- Use `ToolReturn(return_value=..., content=..., metadata=...)` when the application needs a structured return value plus extra model-facing content or app-only metadata.
- Use `ToolReturn[T]` when return-schema generation should infer a schema for `T`; a bare `ToolReturn` intentionally has no constrained return schema.
- `include_return_schema=True` exposes return schemas to the model. It can be set per tool, on `FunctionToolset`, via `.include_return_schemas()`, or through the `IncludeToolReturnSchemas` capability.
- If no return schema can be generated, enabling return schemas can warn or produce no useful guidance; add a concrete return annotation first.

## Approval and Deferred Execution

- Use `requires_approval=True` for tools that always need human approval before execution.
- Raise `ApprovalRequired(metadata=...)` inside a tool when approval depends on arguments or context. After approval, `ctx.tool_call_approved` is `True` and `ctx.tool_call_metadata` contains any metadata supplied with `DeferredToolResults`.
- Raise `CallDeferred(metadata=...)` when an external system should execute the call later. Include `DeferredToolRequests` in the agent or run `output_type` to bubble pending requests to the caller.
- Feed results back with `DeferredToolResults` or `DeferredToolRequests.build_results(...)` using the exact `tool_call_id` values from the prior run.
- Use `ToolApproved(override_args=...)` to approve and alter validated args, `ToolDenied(message=...)` to deny with a model-facing message, `ToolReturn(...)` for rich external call returns, or `ModelRetry(...)` for external-call retry prompts.

## Common Imports

```python
from pydantic_ai import (
    Agent,
    ApprovalRequired,
    CallDeferred,
    DeferredToolRequests,
    DeferredToolResults,
    FunctionToolset,
    ModelRetry,
    RunContext,
    Tool,
    ToolApproved,
    ToolDefinition,
    ToolDenied,
    ToolReturn,
)
from pydantic_ai.models.test import TestModel
```
