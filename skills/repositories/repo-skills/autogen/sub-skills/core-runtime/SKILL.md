---
name: core-runtime
description: "Maintain, debug, and design low-level autogen_core applications:
  runtimes, routed agents, handlers, topics, subscriptions, tools, model
  messages, component config, cancellation, intervention, and distributed
  runtime boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# AutoGen Core Runtime

Use this sub-skill when working on existing AutoGen Python `autogen_core` applications that need low-level event-driven runtime control. AutoGen is in maintenance mode; for new greenfield agent systems, consider Microsoft Agent Framework, but use this skill for AutoGen maintenance, debugging, migration, and compatibility work.

## Route Here For

- `SingleThreadedAgentRuntime` lifecycle, `send_message`, `publish_message`, `stop`, `stop_when_idle`, and runtime state.
- `RoutedAgent`, `message_handler`, `event`, `rpc`, handler type annotations, match predicates, and unhandled messages.
- `DefaultTopicId`, `TopicId`, `AgentId`, `default_subscription`, `type_subscription`, `TypeSubscription`, and topic-to-agent mapping.
- Core `FunctionTool`, `StaticWorkbench`, model messages, chat completion contexts, component serialization, cancellation, and intervention handlers.
- Distributed runtime design, gRPC/protobuf terminology, and when to route implementation work to extension packages.

## Route Elsewhere

- Use `../agentchat-workflows/` for `AssistantAgent`, teams, group chat, high-level tools-as-agents, streaming chat tasks, termination, and AgentChat state.
- Use `../extensions-integrations/` for concrete model clients, `autogen_ext` gRPC runtime packages, Docker/Jupyter executors, MCP, external services, and provider credentials.
- Use `../tools-studio-bench/` for AutoGen Studio, AG Bench, Magentic-One CLI, and `pyautogen` package/version boundary work.

## Core Workflow

1. Identify whether the application is direct RPC (`send_message` to an `AgentId`) or pub/sub (`publish_message` to a `TopicId`).
2. Confirm every agent type is registered before sending, and every publish path has a matching subscription.
3. Start the runtime before enqueueing work, then await `stop()` for direct sends or `stop_when_idle()` after publishes.
4. Keep handlers async, explicitly typed, and decorated; use `message_handler(strict=False)` only when intentionally tolerating type or return mismatches.
5. Treat component loading and `FunctionTool` config as trusted-code operations; validate provider strings, import namespaces, and schemas before loading.

## Bundled References

- `references/api-reference.md` summarizes key low-level APIs and constructor signatures.
- `references/runtime-patterns.md` gives concrete runtime, routing, topics, tools, contexts, cancellation, and intervention patterns.
- `references/distributed-runtime.md` explains distributed/gRPC boundaries without depending on extension packages.
- `references/troubleshooting.md` maps common runtime failures to diagnosis and fixes.
- `scripts/core_runtime_smoke.py` inspects installed signatures and can run a tiny local no-network runtime example.

## Quick Smoke Check

Run the bundled smoke script in an environment with `autogen-core` installed:

```bash
python scripts/core_runtime_smoke.py --inspect
python scripts/core_runtime_smoke.py --run-local-example
```

The local example uses only `SingleThreadedAgentRuntime`, a dataclass message, and an in-process `RoutedAgent`; it performs no network or service calls.
