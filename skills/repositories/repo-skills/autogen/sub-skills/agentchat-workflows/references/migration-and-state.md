# Migration, State, and Serialization

AutoGen AgentChat 0.4+ is a substantial redesign from v0.2. Current maintenance work with 0.7.x should use the layered packages `autogen_agentchat`, `autogen_core`, and `autogen_ext` rather than legacy `autogen.agentchat` imports.

## v0.2 to AgentChat 0.4+ Mapping

| v0.2 concept | 0.4+/0.7.x replacement | Notes |
| --- | --- | --- |
| `from autogen import AssistantAgent` or `autogen.agentchat.AssistantAgent` | `from autogen_agentchat.agents import AssistantAgent` | Supply a concrete `model_client`, not `llm_config`. |
| `llm_config={"config_list": ...}` | `OpenAIChatCompletionClient`, Azure/OpenAI-compatible clients, or `ChatCompletionClient.load_component` | Provider configuration belongs to `../../extensions-integrations/SKILL.md`. |
| `UserProxyAgent` with broad human/code behavior | `UserProxyAgent` for human input; `CodeExecutorAgent` for code execution | Split responsibilities and review executor safety. |
| `initiate_chat` / `GroupChatManager` flows | `agent.run`, `team.run`, `run_stream`, `RoundRobinGroupChat`, `SelectorGroupChat`, `Swarm`, `GraphFlow` | AgentChat is async and task-driven. |
| `register_reply` custom reply hooks | Custom `BaseChatAgent` or lower-level Core routed agents | Use `../../core-runtime/SKILL.md` for custom message routing. |
| Nested chats | `AgentTool`, `TeamTool`, nested `RoundRobinGroupChat`, or explicit teams | Bound nested teams independently. |
| `cache_seed` in LLM config | Model cache wrappers in extensions | Caching is not enabled by default. |

## Migration Steps

1. Replace imports with package-specific modules: `autogen_agentchat` for agents/teams/messages, `autogen_core` for core abstractions, `autogen_ext` for providers and executors.
2. Move model configuration out of `llm_config` into a concrete `ChatCompletionClient` or component config.
3. Convert synchronous chat flows into `async` entrypoints using `await agent.run(...)`, `await team.run(...)`, or `await Console(team.run_stream(...))`.
4. Add deterministic stop conditions to every team: `TextMentionTermination`, `MaxMessageTermination`, `HandoffTermination`, and/or `max_turns`.
5. Split human input, code execution, and model reasoning into separate AgentChat agents where the legacy app mixed them.
6. Replace nested chats with explicit teams or `AgentTool`/`TeamTool` so orchestration is inspectable and stateful.
7. Add state and serialization tests only after no-provider constructor tests pass.

## State Rules

AgentChat agents and teams are stateful by design.

- Pass only new messages/tasks into `run`, `run_stream`, `on_messages`, and `on_messages_stream`; do not resend the full conversation history unless rebuilding a fresh agent/team.
- Call `reset()` when reusing a team/agent for an independent task that should not inherit context.
- Do not use one agent/team instance concurrently from multiple coroutines. Create separate instances for concurrent sessions.
- For web apps, keep per-user or per-session team instances isolated, then persist state between requests when needed.

## Save and Load State

Typical state flow:

```python
state = await team.save_state()
# persist `state` as JSON-compatible data
restored_team = build_team_with_same_names_and_structure()
await restored_team.load_state(state)
```

Important constraints:
- Restore into the same logical structure: same participant names, team types, and compatible message types.
- Save state captures runtime conversation state, not all Python callables or external service configuration.
- Termination conditions also carry state; reset them when reusing after they have fired.
- For `AgentTool` and `TeamTool`, use their state helpers when maintaining nested tool state.

## Component Serialization

For declarative configs, components may support:

```python
config = component.dump_component()
component2 = ComponentType.load_component(config)
```

Use serialization for stable, component-backed settings such as participants, model-client component configs, termination conditions, and teams. Avoid assuming arbitrary Python callables survive serialization.

Notable limitations:
- `UserProxyAgent.input_func` is not serialized; loaded config restores no custom input function.
- `SelectorGroupChat.selector_func` and `candidate_func` are code hooks, not serializable component config.
- `AssistantAgent.tool_call_summary_formatter` is not serializable; prefer `tool_call_summary_format` for config files.
- `AssistantAgent.output_content_type` structured output can limit component round-trip support; test before shipping serialized configs.
- Custom message types must be supplied through `custom_message_types` when loading teams that may encounter them.

## Nested Teams and Tools During Migration

For legacy nested chat flows:
- Use `AgentTool` when a specialist agent should be callable by a main assistant.
- Use `TeamTool` when a bounded multi-agent process should be callable as one tool.
- Use nested `RoundRobinGroupChat` when team outputs should participate as speakers in a larger team.
- Avoid nesting unbounded selector/swarm teams inside tools; add `MaxMessageTermination` and `max_turns` at each level.

## Migration Review Checklist

- Imports use `autogen_agentchat`, `autogen_core`, and `autogen_ext` intentionally.
- Every team has a deterministic stop path.
- Provider setup is separated from orchestration code and can be mocked or replayed.
- Human input is isolated through `UserProxyAgent` or explicit app UI callbacks.
- Code execution requires an explicit executor and, for unsafe contexts, an `approval_func`.
- State persistence restores into matching team/agent structures.
- Serialized configs avoid non-serializable callables or reattach them in code.
