# Core Runtime API Reference

This reference covers the low-level APIs most often needed when maintaining AutoGen `autogen_core==0.7.x` applications.

## Runtime and Agent Identity

| API | Signature or shape | Use | Notes |
| --- | --- | --- | --- |
| `SingleThreadedAgentRuntime` | `SingleThreadedAgentRuntime(intervention_handlers=None, tracer_provider=None, ignore_unhandled_exceptions=True)` | Local development/runtime for in-process agents. | Start before use; await `stop()` or `stop_when_idle()` so background handler failures surface. |
| `AgentId` | `AgentId(type, key)` | Concrete destination or sender identity. | `type` must match a registered runtime type; `key` separates instances under a type. |
| `DefaultTopicId` | `DefaultTopicId(type="default", source=None)` | Standard publish topic. | If `source` is omitted, current subscription context can provide a source; explicit source is easier to debug. |
| `runtime.send_message` | `await runtime.send_message(message, recipient=AgentId(...), sender=None, cancellation_token=None, message_id=None)` | Direct RPC-style call. | Returns the handler response or raises recipient/handler exceptions. |
| `runtime.publish_message` | `await runtime.publish_message(message, topic_id, sender=None, cancellation_token=None, message_id=None)` | Fan-out event publication. | Does not return handler responses; use `stop_when_idle()` to drain queued work. |
| `runtime.register_factory` | `await runtime.register_factory(type, agent_factory, expected_class=None)` | Low-level factory registration. | Prefer `AgentClass.register(runtime, type, factory)` when using `RoutedAgent` decorators. |
| `runtime.register_agent_instance` | `await runtime.register_agent_instance(agent_instance, agent_id)` | Register one concrete instance. | Usually prefer `AgentClass.register_instance(...)` when available. |

`SingleThreadedAgentRuntime` is suitable for standalone apps and tests, not high-throughput distributed systems. Its `ignore_unhandled_exceptions` flag controls whether exceptions from publish handlers are stored and re-raised on a later `process_next`, `stop`, `stop_when_idle`, or `stop_when` call. Direct `send_message` exceptions are tied to the returned awaitable.

## Routed Agents and Handlers

| API | Signature or shape | Use | Notes |
| --- | --- | --- | --- |
| `RoutedAgent` | `RoutedAgent(description)` | Base class that dispatches messages by exact message type and optional predicate. | Subclasses add decorated async methods; do not override `on_message_impl` for normal routing. |
| `message_handler` | `message_handler(func=None, strict=True, match=None)` | Generic handler for event and RPC messages. | Requires `async def`, typed `message`, typed `ctx`, and a return type annotation. |
| `event` | `event(func=None, strict=True, match=None)` | Handler intended for publish/event messages. | Return type should be `None`. |
| `rpc` | `rpc(func=None, strict=True, match=None)` | Handler intended for direct/RPC messages. | Return type should match what callers expect from `send_message`. |
| `MessageContext` | Handler argument `ctx` | Access sender, topic, RPC flag, cancellation token, and message id. | `ctx.topic_id` is usually present for publish and absent for direct send. |

Handler routing uses exact Python runtime types, not subclass matching. If multiple handlers target the same message type, `match` predicates provide secondary routing; the first matching handler in method-name order is used.

## Topics and Subscriptions

| API | Signature or shape | Use | Notes |
| --- | --- | --- | --- |
| `default_subscription` | Decorator or factory with default topic type. | Subscribe an agent type to the default topic. | Relies on registration context if `agent_type` is not explicit. |
| `type_subscription` | `type_subscription(topic_type)` | Decorator that subscribes a routed agent class to one topic type. | Maps matching topic source to agent key through a `DefaultSubscription`. |
| `TypeSubscription` | `TypeSubscription(topic_type, agent_type, id=None)` | Explicit subscription object. | `is_match()` checks only `TopicId.type`; `map_to_agent()` uses `TopicId.source` as `AgentId.key`. |

A common maintenance mistake is registering an agent type and publishing to a topic without adding a matching subscription. Registration makes the type constructible; subscription makes it reachable through `publish_message`.

## Tools and Workbenches

| API | Signature or shape | Use | Notes |
| --- | --- | --- | --- |
| `FunctionTool` | `FunctionTool(func, description, name=None, global_imports=[], strict=False)` | Wrap a typed Python function as a core tool. | Function parameters and return need annotations; config loading executes code from trusted configs only. |
| `StaticWorkbench` | `StaticWorkbench(tools, tool_overrides=None)` | Stable collection of tools. | `list_tools()` returns schemas; `call_tool()` returns a `ToolResult`, not a raw value. |
| `CancellationToken` | `CancellationToken()` | Propagate cancellation through runtime and tools. | Link it to futures only once per operation; pass it into long-running work where supported. |

Use `FunctionTool(strict=True)` when the downstream model/client requires structured-output-compatible schemas with only explicit function arguments and no defaults.

## Model Messages and Contexts

| API | Signature or shape | Use | Notes |
| --- | --- | --- | --- |
| `UserMessage` | `UserMessage(content, source)` | User or external input for model clients. | `content` may be text or mixed text/image content. |
| `AssistantMessage` | `AssistantMessage(content, thought=None, source)` | Model output message. | `content` may be text or function calls; `thought` is optional reasoning text. |
| `BufferedChatCompletionContext` | `BufferedChatCompletionContext(buffer_size, initial_messages=None)` | Keep the most recent N model messages. | `buffer_size` must be positive. |
| `TokenLimitedChatCompletionContext` | `TokenLimitedChatCompletionContext(model_client, token_limit=None, tool_schema=None, initial_messages=None)` | Keep messages within a token budget. | Requires a model client that implements token counting and remaining-token methods. |

Concrete model clients live in integrations packages; this sub-skill covers only the core message/context contracts.

## Component Serialization

Components dump to a `ComponentModel` with `provider`, `component_type`, version fields, optional label/description, and validated `config`. Loading resolves the provider, checks trusted namespaces, imports the provider class, and calls `_from_config`.

Important provider rules:

- Prefer public provider overrides such as `autogen_core.tools.FunctionTool` and `autogen_core.tools.StaticWorkbench` over internal module paths.
- Do not dump local classes; providers containing `<locals>` cannot be loaded reliably.
- Only load configs from trusted sources. `FunctionTool` loading executes configured imports and function source code.
- For custom providers outside first-party namespaces, use `AUTOGEN_ALLOWED_PROVIDER_NAMESPACES` deliberately rather than bypassing trust checks in code.
