---
name: agent-core
description: "Route ROSA installation, model configuration, construction,
  invocation, streaming, history, and executor controls."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ROSA agent core

Use this route when the task is to install or import the Python package, create a
`ROSA` agent, select a tool-calling LangChain chat model, invoke it, stream
events, reset conversation state, inspect token behavior, or bound iterations.
This route covers the agent lifecycle, not the detailed ROS tool catalog.

## First checks

1. Install the distribution with `python -m pip install jpl-rosa` in a Python
   `>=3.9,<4` environment.
2. Import the public API with `from rosa import ROSA, RobotSystemPrompts,
   ChatModel`. The distribution is `jpl-rosa`; the import package is `rosa`.
3. Remember that pip installation does **not** install ROS middleware. ROSA
   construction loads the selected ROS 1 or ROS 2 tool family, so the matching
   ROS Python modules/runtime must be installed and sourced separately.
4. Supply a LangChain chat model that supports tool calling. Do not run a live
   model or ROS system merely to inspect this skill.

For exact signatures and event shapes, read [api-reference.md](references/api-reference.md).
Use [workflows.md](references/workflows.md) for sync/async lifecycle recipes and
[llm-configuration.md](references/llm-configuration.md) for provider setup.
Start with [troubleshooting.md](references/troubleshooting.md) when construction
or execution fails.

## Common lifecycle

```text
install jpl-rosa -> import rosa -> configure tool-calling model
       -> construct ROSA(ros_version=1 or 2, llm=...)
       -> choose invoke() or astream()
       -> inspect/clear chat_history as needed
```

- Choose `ros_version=1` for ROS 1 or `ros_version=2` for ROS 2; then follow
  [ros1-operations](../ros1-operations/SKILL.md) or
  [ros2-operations](../ros2-operations/SKILL.md), respectively.
- Use `invoke(query)` for a complete synchronous string. Ordinary exceptions
  are converted to an `An error occurred: ...` string; `KeyboardInterrupt` is
  propagated.
- Use `astream(query)` only on an instance created with `streaming=True`, and
  consume every event in order. Handle `token`, `tool_start`, `tool_end`,
  `final`, and `error` event types.
- Chat history accumulates successful query/answer pairs by default. Use
  `accumulate_chat_history=False` for stateless calls and `clear_chat()` to
  reset an existing conversation.
- `show_token_usage` is effective only for non-streaming OpenAI/Azure models;
  it is automatically disabled for streaming and for other model classes.
- `max_iterations`, `verbose`, and `return_intermediate_steps` are executor
  controls. The public `invoke()` result remains the output string even when
  intermediate steps are requested.

## Route boundaries

- For ROS 1/ROS 2 graph inspection and actions, use the sibling routes above;
  do not invent entity names or bypass discovery.
- For `tools`, `tool_packages`, `blacklist`, custom robot prompts, or extending
  the tool registry, use [tool-customization](../tool-customization/SKILL.md).
- For package-wide prerequisites and cross-cutting environment checks, return
  to the [rosa root route](../../SKILL.md).
- Keep credentials, model calls, ROS launches, Docker/TurtleSim, and destructive
  robot actions out of installation or documentation checks.
