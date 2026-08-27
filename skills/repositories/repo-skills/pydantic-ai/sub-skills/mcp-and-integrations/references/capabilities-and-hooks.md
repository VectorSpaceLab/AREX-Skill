# Capabilities and Hooks

Use this reference when an integration should travel as a reusable agent behavior bundle: instructions, model settings, tools/toolsets, native tools, wrapper toolsets, lifecycle hooks, event stream processing, or history processing.

## Capability Building Blocks

| API | Use when | Key behavior |
| --- | --- | --- |
| `Capability` | A small integration bundles instructions plus local tools/toolsets. | Mirrors `Agent` tool decorators and supports `defer_loading=True`. |
| `AbstractCapability` | A reusable library integration needs hooks, model settings, native tools, wrapper toolsets, event/history processing, or custom ordering. | Override `get_*` methods and hook methods directly. |
| `Hooks` | Application code needs logging, metrics, validation, approval handling, or lightweight interception without defining a class. | Register functions by constructor kwargs or `hooks.on.*` decorators. |
| `NativeOrLocalTool` | An integration has a provider-native feature plus a local fallback. | Keeps only the native or local path per model request. |
| `MCP`, `WebSearch`, `WebFetch`, `ImageGeneration`, `XSearch` | Built-in adaptive integration capabilities. | Expose native tools where supported and local fallbacks where configured/installed. |
| `Instrumentation` | Agent runs should emit OpenTelemetry/Logfire spans. | Wraps runs, model requests, tools, and output processing. |
| `ProcessHistory`, `ProcessEventStream`, `ReinjectSystemPrompt` | Integration needs history/event/system-prompt adaptation. | Apply narrowly; verify ordering with adjacent capabilities. |

Capabilities are passed through `Agent(..., capabilities=[...])` or per-run `agent.run(..., capabilities=[...])`. Use `AgentSpec.capabilities` only for serializable built-ins that expose `from_spec`; function-backed capabilities and arbitrary callables do not round-trip through JSON/YAML specs.

## Packaging an Integration as a Capability

Use `Capability` for most app-level bundles:

```python
from pydantic_ai.capabilities import Capability

refunds = Capability(
    id='refunds',
    description='Refund status checks and refund approval workflow.',
    instructions='Always confirm the order ID before issuing a refund.',
    defer_loading=True,
)

@refunds.tool_plain
def refund_status(order_id: str) -> str:
    """Return refund status for an order."""
    return f'{order_id}: pending'
```

Escalate to `AbstractCapability` when the integration must:

- contribute provider-native tools or model settings;
- wrap model requests, tool validation/execution, output validation/processing, or runs;
- add wrapper toolsets around other toolsets;
- process event streams or message history;
- require explicit middleware ordering relative to other capabilities;
- isolate per-run mutable state with `for_run()`.

Keep capability state serializable or clearly runtime-only. Durable adapters and `AgentSpec` are sensitive to closures, local object identity, and hidden non-serializable state.

## Deferred Capabilities

Set `defer_loading=True` when a workflow is expensive in prompt tokens, exposes many tools, or should be hidden until needed.

Rules:

- Set a stable, explicit `id`; history replay matches loaded capability state by ID.
- Provide a concise `description`; it appears in the capability catalog so the model can decide when to load it.
- Understand the activation boundary: instructions, function tools, native tools, model settings, and hooks all activate as one unit after the model calls `load_capability`.
- Expect function tools and native tools to appear on the next model request after loading, not in the same provider request that called `load_capability`.
- Reconstruct resumed agents with the same capability IDs; message history stores loaded IDs, not the capability implementation.
- Keep sensitive instructions always-on rather than deferred if exposing them as a `load_capability` tool result would leak them into UI-visible history.

Useful `RunContext` fields for integration callbacks:

- `ctx.loaded_capability_ids`: IDs loaded from current or replayed history.
- `ctx.available_capability_ids`: always-on plus currently loaded capability IDs.
- `ctx.capability_loaded`: true only in callbacks owned by the currently loaded deferred capability.
- `ctx.available_tool_names`: function tools currently known to the run; early hooks may see history-derived values before the current request is assembled.
- `ctx.discovered_tool_names`: deferred function tools discovered by tool search, separate from capability loading.

## Hooks Lifecycle

`Hooks` is the quick path for lifecycle integration:

```python
from pydantic_ai.capabilities import Hooks

hooks = Hooks(id='audit-hooks')

@hooks.on.before_model_request
async def add_audit_metadata(ctx, request_context):
    request_context.model_settings = request_context.model_settings
    return request_context
```

Hook groups:

- Run hooks: `before_run`, `after_run`, `run`, `run_error`.
- Node hooks: `before_node_run`, `after_node_run`, `node_run`, `node_run_error`.
- Event stream hooks: `run_event_stream`, `event`.
- Model request hooks: `before_model_request`, `after_model_request`, `model_request`, `model_request_error`.
- Tool hooks: `prepare_tools`, `prepare_output_tools`, `before_tool_validate`, `after_tool_validate`, `tool_validate`, `tool_validate_error`, `before_tool_execute`, `after_tool_execute`, `tool_execute`, `tool_execute_error`.
- Output hooks: `before_output_validate`, `after_output_validate`, `output_validate`, `output_validate_error`, `before_output_process`, `after_output_process`, `output_process`, `output_process_error`.
- Deferred tool hook: `deferred_tool_calls` to resolve approval or external-execution requests inline.

Ordering and state rules:

- Multiple `before_*` hooks run in registration/capability order.
- Multiple `after_*` hooks run in reverse order.
- `wrap_*` hooks nest as middleware; the first registered wrapper is outermost.
- `CapabilityOrdering(position='outermost'|'innermost', wraps=..., wrapped_by=..., requires=...)` controls composition when order matters.
- Hook timeouts raise `HookTimeoutError`.
- Error hooks use raise-to-propagate and return-to-recover semantics.
- `ModelRetry` used as control flow from wrapper hooks bypasses the corresponding error hook.
- Tool validation/execution hooks run for function tools, not internal structured-output tools.
- During streaming, output validation hooks can fire on partial validation attempts; use `ctx.partial_output` to avoid expensive work on partials.
- When manually iterating an agent graph, use `await run.next(node)` rather than bare iteration if node hooks or pending-message queues must be honored.

On-demand hook caveats:

- Deferred hooks do not fire before their owning capability is loaded.
- Run-scoped hooks (`before_run`, `wrap_run`) are bound at run start, so a capability loaded mid-run will not get those hooks until a later resumed run where history marks it loaded at start.
- Per-step hooks can fire from the next step after loading.
- `after_run` fires if the capability was loaded at any point during the run.

## Logfire and OpenTelemetry

Pydantic AI supports observability through OpenTelemetry; Logfire is the hosted platform and SDK path most users reach for.

Use one of these approaches:

- Global Logfire setup: configure Logfire, then call `logfire.instrument_pydantic_ai()` before running agents.
- Capability setup: pass `Instrumentation()` in `capabilities=[...]` when you want instrumentation to be a normal capability and configurable per agent/spec.
- Plain OTel setup: configure an OTel tracer/logger provider and use Pydantic AI instrumentation settings without sending data to Logfire.

Guidelines:

- Install the `logfire` optional dependency before importing Logfire-specific SDK APIs.
- Do not claim traces are visible in a backend unless the SDK/backend has been configured and credentials are present.
- Use `Instrumentation(settings=InstrumentationSettings(...))` to control content capture, binary content, versioned semantic conventions, event mode, or aggregated usage attribute names.
- Other capabilities can add current-span attributes through standard OpenTelemetry APIs.
- Avoid capturing prompts, outputs, file data, or tool return payloads in regulated environments unless `include_content` policy allows it.

## Web Search and Web Fetch Capabilities

`WebSearch` and `WebFetch` are integration-bound capabilities when an agent needs native provider tools with local fallback behavior.

`WebSearch` choices:

- Native path uses `WebSearchTool` where the selected model/provider supports it.
- `local='duckduckgo'` or `local=True` uses the DuckDuckGo common tool and requires its optional extra.
- `blocked_domains`, `allowed_domains`, and `max_uses` require native support; they should not be silently assumed for local fallback.

`WebFetch` choices:

- Native path uses `WebFetchTool` where supported.
- `local=True` uses the markdownify-based fetch common tool and requires the `web-fetch` extra.
- `allowed_domains` and `blocked_domains` can be enforced locally; `max_uses`, citations, and content-token limits are native-oriented.

Boundary: route generic provider-native tool selection and provider support tables to `../models-and-providers/SKILL.md`; keep this reference for capability-level composition and fallback behavior.

## Capability Design Checklist

Before shipping an integration capability:

- Give every deferred capability and durable-relevant toolset a stable `id`.
- Keep descriptions specific and short enough to guide model routing.
- Decide whether instructions are safe to expose in message history if deferred.
- Verify hook order with adjacent capabilities and wrapper toolsets.
- Use local/no-network tests with `TestModel` or in-process toolsets before live providers.
- Record optional extras and service requirements in troubleshooting rather than hiding them in broad install instructions.
