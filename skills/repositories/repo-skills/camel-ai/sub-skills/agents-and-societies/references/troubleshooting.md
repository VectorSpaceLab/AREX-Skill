# Agents And Societies Troubleshooting

Use this page when CAMEL agent workflows fail, loop forever, terminate too early, or behave differently in CI than in an interactive environment.

## Missing Model Or API Keys

Symptoms:

- `ChatAgent(...)` constructs, but `.step()` fails with authentication, provider, or default model errors.
- `RolePlaying(...)` fails during initialization when `with_task_specify=True` or `with_task_planner=True`.
- `Workforce.process_task(...)` fails before any worker output appears.

Diagnosis:

1. Confirm whether the failing line actually calls a model. Constructors may call models indirectly when task specification/planning is enabled.
2. Route provider selection, `ModelFactory`, backend URLs, API keys, local model endpoints, retries, and model enums to `../../models-and-configuration/`.
3. For CI without credentials, disable model-calling initialization: `with_task_specify=False`, `with_task_planner=False`, and do not call `.step()` or `.process_task()`.
4. Use `../scripts/inspect_agent_basics.py --json` to prove the installed package and object wiring without credentials.

## Invalid `system_message` Type

Symptoms:

- `TypeError`, `AttributeError`, or missing `.content`/`.role_name` around agent setup.
- `RolePlaying` raises that a provided assistant or user agent has `None` system message.

Fix:

- Pass a plain string or a `BaseMessage`, not an arbitrary dict.
- Prefer `BaseMessage.make_system_message(...)` for `ChatAgent` system prompts.
- For `RolePlaying(assistant_agent=..., user_agent=...)`, ensure both pre-built agents were constructed with non-`None` system messages.
- If changing `agent.output_language`, remember it clears message history by regenerating the system message.

## Tool Schema Or Tool Execution Errors

Symptoms:

- Tool schema conversion errors before the model call.
- Tool call loops, wrong argument names, or external tool requests returned to the caller.
- Long/sensitive tool output pollutes agent memory.

Routing and fixes:

- Use this sub-skill only to decide where tools attach: `tools=[...]`, `external_tools=[...]`, `tool_execution_timeout`, and `mask_tool_output`.
- Route `FunctionTool`, schema synthesis, MCP clients, runtime sandboxing, and service credentials to `../../tools-runtimes-and-services/`.
- Set `tool_execution_timeout` for every non-trivial tool.
- Use `mask_tool_output=True` for sensitive or verbose tool results.
- Keep `max_iteration` finite so a tool-calling agent cannot loop indefinitely.

## Infinite Loops And Missing Termination

Symptoms:

- `ChatAgent.step()` repeatedly calls the model or tools.
- Role-playing sessions never emit the task-done phrase.
- Workforce keeps decomposing/retrying without reaching a final result.

Fix:

1. Set `ChatAgent(max_iteration=N)` for every model-calling agent in the workflow.
2. Add `ResponseWordsTerminator` or another terminator and explicitly tell the model to emit the termination signal.
3. In role-play loops, add a hard Python turn limit and break on `assistant_response.terminated`, `user_response.terminated`, or a sentinel such as `CAMEL_TASK_DONE`.
4. In Workforce, set `task_timeout_seconds` and a bounded `failure_handling_config.max_retries`.
5. If auto-decomposition is unstable, switch to `WorkforceMode.PIPELINE` and explicit dependencies.

## Token Limit, Window, And Summarization Problems

Symptoms:

- Long conversations forget instructions or consume too many tokens.
- Summaries dominate the context.
- Tool outputs cause token overflow.

Fix:

- Use `message_window_size` to keep only recent turns.
- Use `token_limit` to cap the context below a model maximum when needed.
- Tune `summarize_threshold` and `summary_window_ratio`; lower thresholds summarize earlier, while a lower summary ratio limits summary footprint.
- Consider `prune_tool_calls_from_memory=True` only when historical tool traces are not needed.
- Route persistent memory, retrieval, vector memory, and `ChatHistoryMemory` internals to `../../memory-rag-and-data/`.

## Workforce Timeout Or Failure Handling

Symptoms:

- A Workforce task remains pending/running.
- Workers repeatedly fail the same task.
- Dynamic worker creation makes debugging unpredictable.

Fix:

1. Print or log the `Task` tree with `task.to_string(state=True)` and results with `task.get_result()`.
2. Set `task_timeout_seconds` low during debugging.
3. Pass `failure_handling_config={"max_retries": 1, "enabled_strategies": ["retry", "replan"], "halt_on_max_retries": False}` to observe behavior without runaway loops.
4. Provide explicit `coordinator_agent`, `task_agent`, and worker agents with bounded `max_iteration`.
5. Use `WorkforceMode.PIPELINE` when the task graph is known.
6. Disable or isolate `share_memory` if workers appear to inherit stale context.
7. Add callbacks or `stream_callback` for observability; callbacks should be fast and exception-safe.

## Async And Streaming Callback Misuse

Symptoms:

- Coroutine was never awaited warnings.
- Stream callback receives repeated cumulative text when delta text was expected.
- UI or logs hang during streaming.

Fix:

- Await async APIs: `await agent.astep(...)` and `await workforce.process_task_async(...)`.
- Do not call async APIs from sync code without a clear event-loop boundary such as `asyncio.run(...)` at the top level.
- Set `stream_accumulate` intentionally on `ChatAgent` when downstream code needs either deltas or accumulated content.
- Keep `on_request_usage`, `stream_callback`, and `WorkforceCallback` implementations short; offload slow work to queues/loggers.
- Catch and log callback exceptions so observability code does not break the agent loop.

## State And Memory Confusion

Symptoms:

- Agent remembers previous tasks unexpectedly.
- Role-playing clones carry or lose memory unexpectedly.
- Workforce workers contaminate each other’s context.

Fix:

- Call `agent.reset()` before reusing an agent for a new independent conversation.
- Use `RolePlaying.clone(with_memory=False)` for fresh sessions and `with_memory=True` only when continuity is desired.
- In Workforce, use `share_memory=False` for isolation; enable it only with a documented trace-sharing reason.
- If swapping `agent.memory`, confirm that the system message is preserved and the new memory does not contain incompatible records.
- Keep task identity explicit with stable `Task(id=...)` values when debugging dependencies.

## RolePlaying Initialization Surprises

Symptoms:

- `RolePlaying(...)` calls a model before the first explicit `step()`.
- Custom assistant/user agents are ignored or raise validation errors.
- Critic mode changes which message continues the loop.

Fix:

- Set `with_task_specify=False` and `with_task_planner=False` when initialization must be credential-free.
- Pass `assistant_agent_kwargs`, `user_agent_kwargs`, `task_specify_agent_kwargs`, and `task_planner_agent_kwargs` when different internal agents need different models or limits.
- When supplying `assistant_agent` or `user_agent`, ensure each has a concrete system message.
- With `with_critic_in_the_loop=True`, expect candidate messages to be reduced by the critic; inspect both `.msgs` and selected `.msg`.

## Task Object Pitfalls

Symptoms:

- New tasks show `FAILED` state before execution.
- Decomposition returns no subtasks.
- Parent task result stays empty after subtasks complete.

Fix:

- CAMEL 0.2.91a4 initializes `Task.state` as `TaskState.FAILED`; do not treat initial state as final failure without workflow context.
- `Task.decompose(agent=...)` expects model output in `<task>...</task>` blocks. Validate the prompt and parser.
- Use `task.update_result(result)` to mark a task `DONE`.
- Use `task.compose(agent=...)` only after subtasks have meaningful results.
- Use `TaskManager.set_tasks_dependence(...)` or Workforce pipeline builders for dependency graphs instead of ad hoc lists.

## Quick Triage Checklist

- Can `python sub-skills/agents-and-societies/scripts/inspect_agent_basics.py --json` import CAMEL and inspect signatures?
- Is a model call happening earlier than expected through task specification, task planning, `.step()`, `.decompose()`, or `process_task()`?
- Are all model-calling agents bounded with `max_iteration`, `step_timeout`, and workflow-level turn/time limits?
- Are provider credentials and backend settings handled by `../../models-and-configuration/`?
- Are tool schema/runtime issues handled by `../../tools-runtimes-and-services/`?
- Are memory/retrieval internals handled by `../../memory-rag-and-data/`?
