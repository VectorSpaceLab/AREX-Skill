# Agent API reference

This reference describes the public DB-GPT 0.8.1 agent surface as exposed by the
installed `dbgpt` package. It is an operating reference, not a copy of the source
tree. Prefer public package imports and inspect the installed version before relying on
an optional class.

## Agent construction and lifecycle

The core exports are available from `dbgpt.agent`:

```python
from dbgpt.agent import (
    AgentContext,
    AgentGenerateContext,
    AgentMessage,
    AgentMemory,
    ConversableAgent,
    LLMConfig,
    ProfileConfig,
    UserProxyAgent,
)
```

`ConversableAgent` is a configurable `Role` implementing the `Agent` protocol. Its
live constructor requires a `ProfileConfig` unless a subclass defines a class-level
profile. Important constructor fields include:

| Field | Meaning / default |
|---|---|
| `profile` | Required profile configuration for a plain `ConversableAgent`. |
| `agent_context` | Optional until bound; `build()` requires it for normal execution. |
| `memory` | `AgentMemory` created by default. |
| `actions` | Empty list by default; a non-human, non-team agent normally needs an action. |
| `resource` | Optional `Resource`/`ResourcePack` supplied to actions. |
| `llm_config` | Optional `LLMConfig`; required for a non-human, non-team agent. |
| `run_mode` | `default` or `loop` (`AgentRunMode`). |
| `max_retry_count` | `3`. |
| `max_timeout` | `600` seconds. |
| `stream_out` / `show_reference` | `True` / `False`. |

A safe binding sequence is:

```python
profile = ProfileConfig(
    name="LocalAssistant",
    role="Assistant",
    goal="Answer the user's request using the supplied capabilities.",
    desc="A deterministic example assistant profile.",
)
context = AgentContext(
    conv_id="local-example",
    language="en",
    max_chat_round=10,
    max_retry_round=2,
    max_new_tokens=512,
)

agent = ConversableAgent(profile=profile)
agent.bind(context)
agent.bind(memory)                 # optional replacement AgentMemory
agent.bind(tool_pack)              # when an action consumes tools
agent.bind(MyAction)               # action class or instance
agent.bind(skill)                  # optional Skill; sets bind_prompt
agent.bind(llm_config)             # required for a model-backed agent
built = await agent.build()
```

`bind(target)` returns the same agent and recognizes these target types:

- `LLMConfig` -> `llm_config`;
- `AgentContext` -> `agent_context`;
- `Resource` -> `resource`;
- `AgentMemory` -> `memory`;
- `ProfileConfig` -> `profile`;
- `Action` subclass or action instance -> appended to `actions`;
- a list of action classes/instances -> appended to `actions`;
- a `SkillBase` (including a file-based skill converted by DB-GPT) -> `_skill` and,
  when present, `bind_prompt`;
- `PromptTemplate` -> `bind_prompt`.

Bind context, model config, resources, and actions before `build()`. `build()` is
async: it preloads the resource, invokes `check_available()`, initializes action
resources, wraps the configured model client, initializes and clones agent memory, and
recovers prior history for the conversation. A resource preload can do I/O, so it is
not part of a pure construction check.

### Availability checks

`check_available()` is a useful preflight and raises `ValueError` rather than silently
constructing a partially usable agent. It checks:

1. profile/identity;
2. that `agent_context` exists;
3. for every action with `resource_need`, that a resource of that type is available;
4. for non-human, non-team agents, that actions exist and an LLM config/client is
   available.

A `UserProxyAgent` is the normal human-side participant and can be built with context
and memory without an LLM. A model-backed agent needs an actual client supplied through
`LLMConfig`; this route does not invent a provider or make a network call.

`blocking_func_to_async(func, *args, **kwargs)` runs synchronous functions through the
agent executor and awaits coroutine functions directly. Use it for blocking local
work rather than blocking the event loop in an async action.

## Profiles and prompts

`ProfileConfig` contains `name`, `role`, `goal`, `retry_goal`, `constraints`,
`retry_constraints`, `desc`, `expand_prompt`, `examples`, and system/user/write-memory
templates. The normal profile templates are Jinja-compatible. `ProfileConfig.create_profile()`
resolves dynamic configuration and returns the profile used by `Role.current_profile`.

Useful calls:

```python
real_profile = profile.create_profile(prefer_prompt_language="en")
system_prompt = real_profile.format_system_prompt(question="What can you do?")
user_prompt = real_profile.format_user_prompt(question="Check this input")
```

`Role.build_prompt(is_system=True|False, ...)` is the normal async prompt path. The
sandboxed Jinja environment limits template behavior. Runtime values can be supplied
through the documented template variables (`question`, `most_recent_memories`,
`resource_prompt`, `expand_prompt`, `constraints`, `examples`, and output schema
values). Avoid inserting untrusted strings into a new template; pass them as values.

A bound core `Skill` can supply a `PromptTemplate` as `bind_prompt`. Binding it is not
the same as validating or loading the skill's required resources; do those checks in
the application or skill-aware middleware before the model call.

## Messages and generate context

`AgentMessage` is a dataclass with these important fields:

```text
content, name, rounds, context, action_report, review_info,
current_goal, model_name, role, success, resource_info
```

Use `AgentMessage(content="...", role=...)` for local messages. `to_dict()` preserves
agent metadata; `to_llm_message()` deliberately reduces the object to `content`,
`context`, and `role`. `from_llm_message()` and `from_messages()` reconstruct messages
from those reduced/dictionary forms, and `copy()` makes a shallow message copy with a
copied dict context/review info.

`AgentGenerateContext` carries a current message, sender, optional reviewer, retry and
round state, `rely_messages`, memory, `agent_context`, and `llm_client`. Middleware and
AWEL agent operators pass this object between lifecycle phases. Do not assume every
field is populated when writing a hook.

The abstract `Agent` lifecycle is:

```text
send -> recipient.receive -> generate_reply
                       -> thinking -> act -> verify/review as implemented
```

`send()` and `receive()` are async and carry reviewer/recovery/retry/history flags.
`generate_reply()` returns an `AgentMessage`; `act()` returns `ActionOutput`. Concrete
agents decide whether a reply is terminal and how errors are retried. Never treat a
successful Python return from `thinking()` as proof that a model call occurred.

## Memory and context budgets

`AgentMemory` combines the agent memory structure with `GptsMemory`, which stores
conversation/plan records separately. `ShortTermMemory`, `SensoryMemory`,
`LongTermMemory`, and `HybridMemory` are the principal structures. For a small local
fixture, a bounded `ShortTermMemory(buffer_size=...)` is easier to reason about.
Initialize a conversation ID in any `GptsMemory` used for conversation history.

Context management is opt-in. Set `AgentContext.enable_context_management=True` and
call `agent.init_context_management(...)` after the agent is configured, or provide a
`ContextBudgetConfig` directly:

```python
from dbgpt.agent.core.context import ContextBudgetConfig

config = ContextBudgetConfig(
    max_context_tokens=32000,
    reserved_tokens=2048,
    warning_threshold=0.70,
    error_threshold=0.90,
)
agent.init_context_management(config=config, model_name="local-model")
```

The effective budget is `max_context_tokens - reserved_tokens`. The tracker classifies
`NORMAL`, `WARNING`, `ERROR`, `CRITICAL`, and `OVERFLOW` at ratios below 0.70, at/above
0.70, at/above 0.90, at/above 0.95, and at/above 1.0 by default. It counts message
content using `ProxyTokenizerWrapper` and falls back to roughly four characters per
token when token counting is unavailable.

`ContextManager.manage_context(messages, current_round, task_progress=None)` emits
`context.status` events and progressively performs observation truncation, recent-round
retention, and optional LLM summarization. `reactive_compact(messages)` is an emergency
trim for context-too-long failures. Three consecutive compaction failures trip the
tracker circuit breaker by default. Keep budgets and thresholds explicit in tests;
a CPU import check does not verify a provider's real context window.

## Tools, actions, teams, and agent managers

Actions translate model output into effects. `ActionOutput` records `content`, success,
`observations`, action metadata, optional view, retry/termination, and persisted result
path. An action that uses tools normally declares `resource_need == ResourceType.Tool`.
`ToolAction` parses a `ToolInput` containing `tool_name` and `args`; it must receive a
resource containing the named tool.

`Team` stores `agents`, `messages`, and `max_round` (default 100). `hire([...])` adds
agents, `agent_names` reports their roles, `agent_by_name(name)` resolves an exact
match, `append(message)` normalizes mixed text/image content to text, and `reset()`
clears messages. `ManagerAgent` combines team and conversable-agent behavior. The
built-in `PlannerAgent.bind_agents(agents)` sets the planner's agent list and packages
member resources; `AutoPlanChatManager` coordinates plan memory and speaker selection.
Team planning still requires the model-backed planner/manager and should be documented
as provider-dependent.

`AgentManager` is initialized with `initialize_agent(system_app)`, retrieved with
`get_agent_manager(system_app)`, and registers classes using
`register_agent(cls, ignore_duplicate=False)`. Registration instantiates the class to
obtain its role, so a class profile must be constructible without a live model. Lookup
is by role/name; a missing role raises `ValueError`. `scan_agents()` discovers built-in
agent classes, but discovery is application startup behavior rather than a pure unit
fixture.

## Middleware

`AgentMiddleware` exposes async hooks for `before_init`, `after_init`,
`before_generate_reply`, `after_generate_reply`, `before_thinking`, `after_thinking`,
`before_act`, `after_act`, and `modify_system_prompt`. `MiddlewareManager.register()`
appends a middleware once and returns the manager; `unregister()` removes it. Execution
is in registration order, disabled middleware is skipped, and returned dictionaries are
merged for lifecycle hooks. Prompt modifications are applied sequentially, with each
hook receiving the previous prompt.

`MiddlewareAgent` enables middleware with `AgentConfig`. Its build and prompt/action
paths run the corresponding hooks. Hook contexts are newly constructed in several
paths, so use stable message/context fields rather than relying on hidden mutable state.
