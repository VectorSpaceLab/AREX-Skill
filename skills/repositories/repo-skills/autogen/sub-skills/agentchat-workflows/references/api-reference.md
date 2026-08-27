# AgentChat API Reference

This reference summarizes the high-level AgentChat surfaces most often maintained in AutoGen 0.7.x applications. It is intentionally focused on app-level orchestration; route low-level runtime details to `../../core-runtime/SKILL.md` and concrete providers/executors to `../../extensions-integrations/SKILL.md`.

## Agents

| API | Purpose | Constructor and key notes |
| --- | --- | --- |
| `AssistantAgent` | Model-backed assistant with tools, workbenches, handoffs, model context, streaming, structured output, memory, and state. | `AssistantAgent(name, model_client, tools=None, workbench=None, handoffs=None, model_context=None, description=..., system_message=..., model_client_stream=False, reflect_on_tool_use=None, max_tool_iterations=1, tool_call_summary_format="{result}", output_content_type=None, memory=None, metadata=None)`. `tools` and `workbench` are mutually exclusive. Agent state persists between calls; pass only new messages. Not thread-safe/coroutine-safe. |
| `UserProxyAgent` | Human input participant, including handoff reply handling. | `UserProxyAgent(name, description="A human user", input_func=None)`. `input_func` may be sync or async. In streaming, it emits `UserInputRequestedEvent` before returning a `TextMessage` or handoff reply. |
| `CodeExecutorAgent` | Executes markdown code blocks or model-generated code through a configured code executor. | `CodeExecutorAgent(name, code_executor, model_client=None, model_context=None, model_client_stream=False, max_retries_on_error=0, description=None, system_message=..., sources=None, supported_languages=None, approval_func=None)`. Always review executor safety; without `approval_func`, code executes automatically after detection. Concrete executors live in extensions. |

## Teams

| API | Selection pattern | Constructor and key notes |
| --- | --- | --- |
| `RoundRobinGroupChat` | Fixed turn order across agents or nested teams. | `RoundRobinGroupChat(participants, termination_condition=None, max_turns=None, name=None, description=None, runtime=None, custom_message_types=None, emit_team_events=False)`. Without `termination_condition` or `max_turns`, it can run indefinitely. Supports nested `Team` participants. |
| `SelectorGroupChat` | Central selector chooses the next speaker using a model, with optional custom selector/candidate hooks. | `SelectorGroupChat(participants, model_client, selector_prompt=..., allow_repeated_speaker=False, selector_func=None, candidate_func=None, max_selector_attempts=3, termination_condition=None, max_turns=None, model_client_streaming=False, model_context=None, ...)`. Requires at least two participants. `selector_func` may return a valid participant name to skip model selection. `candidate_func` must return a non-empty list of valid names. |
| `Swarm` | Handoff-driven local coordination. | `Swarm(participants, termination_condition=None, max_turns=None, name=None, description=None, runtime=None, custom_message_types=None, emit_team_events=False)`. Participants must be `ChatAgent`s; the first participant must produce `HandoffMessage`. Use with assistant `handoffs`. |
| `MagenticOneGroupChat` | Magentic-One orchestrator manages planning and speaker selection. | `MagenticOneGroupChat(participants, model_client, termination_condition=None, max_turns=20, max_stalls=3, final_answer_prompt=..., ...)`. Participants must be `ChatAgent`s, not nested teams. This is the library team API, not the separate Magentic-One CLI package. |

## Termination

| API | Use | Constructor and behavior |
| --- | --- | --- |
| `TextMentionTermination` | Stop when text appears in a chat message. | `TextMentionTermination(text, sources=None)`. `sources` limits which agent message sources are checked. |
| `MaxMessageTermination` | Bound runs by message count. | `MaxMessageTermination(max_messages, include_agent_event=False)`. Counts chat messages by default; set `include_agent_event=True` if tool/request/event messages should count. |
| `HandoffTermination` | Stop when handoff reaches a target. | `HandoffTermination(target)`. Useful to pause a `Swarm` or handoff workflow for external/human handling. |

Combine termination conditions when the app needs both semantic and hard bounds. For every team under maintenance, verify at least one deterministic stop path.

## Tools as Agents and Teams

| API | Purpose | Constructor and key notes |
| --- | --- | --- |
| `AgentTool` | Expose a `BaseChatAgent` as a callable tool to another assistant. | `AgentTool(agent, return_value_as_last_message=False)`. With `return_value_as_last_message=True`, the wrapped agent's final message becomes the tool return value; otherwise the tool returns a task-result style summary. |
| `TeamTool` | Expose a `Team` as a callable tool. | `TeamTool(team, name, description, return_value_as_last_message=False)`. Use a bounded team inside the tool to avoid hanging the caller. State can be saved/loaded through the tool. |

## Streaming and Results

- `agent.run(task=...)` and `team.run(task=...)` return `TaskResult` with `messages`; the final response is normally the last chat message.
- `run_stream(task=...)` returns an async stream; the final item is the `TaskResult`.
- `AssistantAgent(model_client_stream=True)` additionally yields `ModelClientStreamingChunkEvent` events during model generation.
- `Console(stream)` consumes an AgentChat async stream for terminal display. Do not `await team.run_stream(...)` directly; iterate it or pass it to `Console`.

## Component State and Serialization

- Agents, teams, termination conditions, and tools implement component/state APIs where supported: `save_state`, `load_state`, `dump_component`, and `load_component`.
- Callable fields such as custom `selector_func`, `candidate_func`, `input_func`, and `tool_call_summary_formatter` are not generally serializable. Reattach them in code after loading serialized configs.
- `output_content_type` enables structured final messages but can affect component serialization support; test round trips before relying on YAML/JSON configs.
