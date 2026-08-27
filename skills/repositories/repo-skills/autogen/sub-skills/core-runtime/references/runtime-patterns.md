# Core Runtime Patterns

Use these patterns when maintaining `autogen_core` code. They are intentionally low-level; high-level chat-agent teams belong in `agentchat-workflows`.

## Direct RPC Pattern

Use direct sends when exactly one target agent should handle the message and the caller needs a response.

```python
from dataclasses import dataclass
from autogen_core import AgentId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler

@dataclass
class Request:
    text: str

@dataclass
class Reply:
    text: str

class EchoAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("Echo core agent")

    @message_handler
    async def handle_request(self, message: Request, ctx: MessageContext) -> Reply:
        return Reply(text=message.text)

runtime = SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)
await EchoAgent.register(runtime, "echo", lambda: EchoAgent())
runtime.start()
reply = await runtime.send_message(Request("ping"), recipient=AgentId("echo", "default"))
await runtime.stop()
```

Maintenance checklist:

- The `AgentId.type` must equal the registered type string (`"echo"` above), not the class name unless you registered that string.
- The agent factory must return the expected class and should not capture request-scoped mutable state accidentally.
- The handler must have a concrete message type and concrete return annotation; missing annotations fail during decorator setup.
- Direct send exceptions propagate to the awaited call; do not hide them behind `stop_when_idle()` diagnostics.

## Publish/Subscribe Pattern

Use publish when one event should fan out to zero or more subscribers.

```python
from dataclasses import dataclass
from autogen_core import DefaultTopicId, MessageContext, RoutedAgent, SingleThreadedAgentRuntime, message_handler, type_subscription

@dataclass
class Event:
    text: str

@type_subscription("alerts")
class AlertAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("Alert subscriber")

    @message_handler
    async def handle_event(self, message: Event, ctx: MessageContext) -> None:
        assert ctx.topic_id is not None
        print(message.text)

runtime = SingleThreadedAgentRuntime(ignore_unhandled_exceptions=False)
await AlertAgent.register(runtime, "alert-agent", lambda: AlertAgent())
runtime.start()
await runtime.publish_message(Event("disk full"), DefaultTopicId(type="alerts", source="host-1"))
await runtime.stop_when_idle()
```

Maintenance checklist:

- Publishing to `DefaultTopicId(type="alerts")` reaches only subscriptions whose topic type is `"alerts"`.
- `TypeSubscription` maps `TopicId.source` to the subscriber `AgentId.key`; a new source can create/use a different keyed agent instance.
- `publish_message` returns after enqueueing, not after every handler finishes. Await `stop_when_idle()` or another drain condition.
- If no subscribers match, the publish can appear to succeed while no handler runs; inspect subscriptions before blaming handlers.

## Handler Design

A valid routed handler is an async method with exactly `self`, `message`, and `ctx` parameters, where `message` and return are annotated.

- Use dataclasses or Pydantic models for message payloads so serialization and tests are predictable.
- Use `@message_handler(match=...)` when two handlers share the same exact message type.
- Keep `strict=True` for normal production maintenance; switch to `strict=False` only to observe legacy mismatches while logging warnings.
- Override `on_unhandled_message` only for diagnostics or fallback behavior; do not use it to mask routing bugs.
- Treat union message/return annotations carefully: strict validation checks the concrete runtime type against known target/return types.

## Topic and Agent Identity Design

Choose identifiers deliberately:

- Agent `type`: stable logical implementation category registered with the runtime.
- Agent `key`: logical instance key, often `"default"`, a tenant id, or a topic source.
- Topic `type`: routing channel name used by subscriptions.
- Topic `source`: producer or partition key that `TypeSubscription` maps to an agent key.

For event streams, document which values are stable protocol values and which are operational partitions. Many production bugs come from renaming a topic type in one module and not updating the subscription decorator.

## Tools and Workbenches

Core tools can be used without model-provider setup:

```python
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool, StaticWorkbench

def add(x: int, y: int) -> int:
    return x + y

tool = FunctionTool(add, description="Add two integers")
workbench = StaticWorkbench([tool])
result = await workbench.call_tool("add", {"x": 2, "y": 3}, CancellationToken())
assert not result.is_error
```

Maintenance checklist:

- Every function parameter and return value must be annotated for schema generation.
- `call_tool()` returns a `ToolResult` with content blocks and `is_error`, not the raw function return.
- Tool overrides may rename or re-describe tools; ensure override names do not collide with original tool names or other overrides.
- Loading a dumped `FunctionTool` executes imports and function code; only load trusted serialized tool configs.

## Model Messages and Contexts

Core model contracts are provider-neutral. Use them to inspect or transform messages without pulling in a concrete model client.

- `UserMessage(content=..., source=...)` represents user/external input.
- `AssistantMessage(content=..., source=..., thought=None)` represents model output or function calls.
- `BufferedChatCompletionContext(buffer_size=N)` keeps the last N messages and rejects non-positive buffer sizes.
- `TokenLimitedChatCompletionContext(model_client=..., token_limit=...)` delegates token counting to the supplied model client; route concrete client setup to `extensions-integrations`.

When debugging context truncation, inspect the messages returned by `await context.get_messages()` rather than assuming every added message is still visible.

## Component Config Round Trips

Use component config for portable first-party component definitions, not for arbitrary untrusted code execution.

1. Confirm the object is a component and has a public provider override when possible.
2. Call `dump_component()` and inspect `provider`, `component_type`, `version`, and `config`.
3. Load with the expected class when available, for example `BaseTool.load_component(model)` or `ComponentLoader.load_component(model, ExpectedType)`.
4. If loading fails, check provider string shape, trusted namespace, import availability, and schema validation before modifying application logic.

## Cancellation and Intervention

Cancellation is cooperative:

- Create one `CancellationToken` per operation or request tree.
- Pass it into `send_message`, `publish_message`, tool calls, and long-running handlers.
- In custom long-running code, periodically check or connect the token to cancellable futures.
- Avoid reusing a canceled token across unrelated operations.

Intervention handlers are installed on `SingleThreadedAgentRuntime(intervention_handlers=[...])` and can inspect or modify messages before send/publish delivery. Keep interventions deterministic and well logged; they can make routing bugs look like handler bugs when they drop or transform messages.

## State and Lifecycle

`SingleThreadedAgentRuntime.save_state()` saves instantiated agent state, not the subscription registry. When restoring, register factories/subscriptions first, then load runtime state.

Recommended lifecycle for tests and maintenance scripts:

1. Build runtime with `ignore_unhandled_exceptions=False` while debugging.
2. Register all agents and subscriptions.
3. Start runtime.
4. Send/publish work.
5. Await responses or `stop_when_idle()`.
6. Save state if needed.
7. Await `stop()` and let exceptions surface.
