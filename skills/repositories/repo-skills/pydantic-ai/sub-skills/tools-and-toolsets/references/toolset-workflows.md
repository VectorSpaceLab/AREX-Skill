# Toolset Workflows

Use this reference when a task needs reusable tool groups, dynamic tool catalogs, approval policies, external tool calls, or large-catalog search. For MCP/FastMCP transport setup, route to `../../mcp-and-integrations/SKILL.md`.

## FunctionToolset Pattern

`FunctionToolset` collects local Python functions and can carry shared defaults:

```python
from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.models.test import TestModel

search_tools = FunctionToolset[str](
    id='search',
    instructions=lambda ctx: f'Use search tools for tenant {ctx.deps}.',
    max_retries=2,
    require_parameter_descriptions=True,
    metadata={'domain': 'search'},
)

@search_tools.tool
def lookup(ctx: RunContext[str], query: str) -> str:
    """Search indexed notes.

    Args:
        query: Search phrase to look up.
    """
    return f'{ctx.deps}:{query}'

agent = Agent(TestModel(), deps_type=str, toolsets=[search_tools])
```

Use an `id` when a durable execution adapter needs stable toolset identity. Use `instructions=` or `@toolset.instructions` when a tool group needs usage guidance independent of the agent's main instructions.

## Composition Order

A robust composition order is:

1. Build leaf `FunctionToolset` or `ExternalToolset` instances.
2. Prefix or rename independent catalogs to avoid collisions.
3. Combine catalogs with `CombinedToolset`.
4. Filter by role, tenant, feature flag, or model capability.
5. Prepare definitions for per-step description/schema/metadata edits.
6. Wrap with approval, deferred loading, metadata, or return-schema behavior.

Example:

```python
from dataclasses import replace
from pydantic_ai import CombinedToolset, FunctionToolset, RunContext, ToolDefinition

math_tools = FunctionToolset()
admin_tools = FunctionToolset()


def allow_for_role(ctx: RunContext[str], tool_def: ToolDefinition) -> bool:
    return ctx.deps == 'admin' or not tool_def.name.startswith('admin_')


def add_role_hint(ctx: RunContext[str], tool_defs: list[ToolDefinition]) -> list[ToolDefinition]:
    return [replace(td, description=f'{td.description} Role: {ctx.deps}.') for td in tool_defs]

catalog = (
    CombinedToolset([math_tools.prefixed('math'), admin_tools.prefixed('admin')])
    .filtered(allow_for_role)
    .prepared(add_role_hint)
    .include_return_schemas()
)
```

## Wrapper Toolsets

| Wrapper | Use when | Key behavior |
| --- | --- | --- |
| `CombinedToolset([...])` | Several toolsets should be presented as one catalog | Raises a `UserError` on name conflicts. Prefix or rename before combining. |
| `PrefixedToolset(toolset, 'prefix')` or `.prefixed('prefix')` | Two toolsets may expose the same names | Exposes `prefix_name` externally and maps calls back to original names internally. |
| `RenamedToolset(toolset, {'new': 'old'})` or `.renamed(...)` | Names need targeted changes | Use for planned renames; use prefixing for whole catalogs. |
| `FilteredToolset(toolset, predicate)` or `.filtered(predicate)` | Availability depends on `RunContext` or `ToolDefinition` | Predicate can be sync or async and returns `True` to expose a tool. |
| `PreparedToolset(toolset, prepare)` or `.prepared(prepare)` | Definitions need per-step edits | Can remove tools or replace definitions, but cannot add or rename tools. |
| `ApprovalRequiredToolset(toolset, predicate)` or `.approval_required(predicate)` | Toolset calls require approval based on args/context | Predicate sees `RunContext`, `ToolDefinition`, and validated args. Omit predicate to require approval for every call. |
| `DeferredLoadingToolset` or `.defer_loading(tool_names=None)` | Large catalogs should be hidden until searched | Marks all or selected tools with `defer_loading=True`. Combine with `ToolSearch` for discovery. |
| `IncludeReturnSchemasToolset` or `.include_return_schemas()` | The model benefits from return type information | Sets `include_return_schema=True` on wrapped tool definitions. |
| `SetMetadataToolset` or `.set_metadata(...)` | Downstream filters/selectors need shared metadata | Metadata is app-side only and not shown to the model. |
| `ExternalToolset(tool_defs, id=...)` | A frontend or upstream service executes calls | Tool definitions become `kind='external'`; the agent emits `DeferredToolRequests.calls`. |
| Custom `WrapperToolset` | Tool execution itself needs interception | Override `call_tool` to log, sandbox, rate limit, or alter execution while delegating to `super()`. |

## Dynamic Toolsets

Pass a context-aware factory to `Agent(toolsets=[...])` or register with `@agent.toolset` when the available catalog depends on dependencies or per-run state.

```python
from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.models.test import TestModel

agent = Agent(TestModel(), deps_type=bool)

@agent.toolset
def optional_tools(ctx: RunContext[bool]) -> FunctionToolset[bool] | None:
    if not ctx.deps:
        return None
    toolset = FunctionToolset[bool](instructions='Extra tools are enabled for this run.')

    @toolset.tool_plain
    def extra() -> str:
        """Return a marker from the optional catalog."""
        return 'enabled'

    return toolset
```

Choose dynamic toolsets when the whole catalog changes. Choose `FilteredToolset` when the catalog exists but a subset should be visible.

## Tool Search and Deferred Loading

Use tool search when many tools waste context or reduce provider prompt-cache efficiency.

- Mark tools with `defer_loading=True` on `Tool`, decorators, or `FunctionToolset`; or call `.defer_loading()` on any toolset.
- Add `ToolSearch` from `pydantic_ai.capabilities` when you need explicit strategy control. Pydantic AI also auto-injects the capability with zero overhead when no deferred tools exist.
- `ToolSearch(strategy=None)` lets the current model choose native provider search when supported and local keyword search otherwise.
- `ToolSearch(strategy='keywords')` forces local keyword matching while still using provider client-executed search surfaces where available.
- `ToolSearch(strategy='bm25')` and `'regex'` force named Anthropic native strategies and should not be used for provider-portable agents.
- A callable strategy receives `ctx`, `queries`, and candidate `ToolDefinition` values, and returns matching tool names.

Keep deferred tools discoverable: clear names, specific descriptions, parameter descriptions, and consistent metadata matter more when tools are hidden behind search.

## Approval and External Execution Workflows

For human approval:

1. Register a tool with `requires_approval=True`, wrap a toolset with `.approval_required(...)`, or raise `ApprovalRequired` from the tool body.
2. Ensure the run `output_type` includes `DeferredToolRequests` unless a `HandleDeferredToolCalls` capability resolves all requests inline.
3. Inspect `DeferredToolRequests.approvals` and preserve each `tool_call_id`.
4. Resume with `DeferredToolResults(approvals={tool_call_id: True})`, `ToolApproved(override_args=...)`, or `ToolDenied(message=...)`.

For external execution:

1. Use `ExternalToolset` when definitions come from a UI/upstream service, or raise `CallDeferred` from a normal tool when execution sometimes moves out of process.
2. Ensure `DeferredToolRequests` is in `output_type`.
3. Execute externally using the exact args and `tool_call_id` from `DeferredToolRequests.calls`.
4. Resume with `DeferredToolResults(calls={tool_call_id: value})`, `ToolReturn(...)`, or `ModelRetry(...)`.

Do not put external execution results into `approvals`, and do not put approval decisions into `calls`.

## TestModel Checks

`TestModel` is the quickest no-network check for tool exposure:

```python
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel

toolset = FunctionToolset()

@toolset.tool_plain
def ping() -> str:
    """Return a ping response."""
    return 'pong'

model = TestModel(call_tools=[])
agent = Agent(model, toolsets=[toolset])
agent.run_sync('inspect tools')
assert model.last_model_request_parameters is not None
assert [td.name for td in model.last_model_request_parameters.function_tools] == ['ping']
```

Use `call_tools=[]` when you only need the request parameters. Use `call_tools=['tool_name']` or `'all'` when you need deterministic execution through tool-call handling.
