# AgentChat Workflow Patterns

These patterns are safe starting points for maintaining existing AutoGen AgentChat apps. They avoid credential-dependent calls unless a concrete model client is already configured elsewhere.

## Single Assistant

Use `AssistantAgent` when one model-backed agent owns the task.

```python
from autogen_agentchat.agents import AssistantAgent

assistant = AssistantAgent(
    name="assistant",
    model_client=model_client,
    system_message="You are a concise maintenance assistant.",
    model_client_stream=True,
)
result = await assistant.run(task="Summarize the issue.")
print(result.messages[-1].to_text())
```

Maintenance checks:
- Pass only new task/messages to each run; the agent keeps its own context.
- Do not call the same agent concurrently from multiple coroutines.
- Configure model clients and credentials through `../../extensions-integrations/SKILL.md`.

## Tool-Using Assistant

Use plain callables or `BaseTool` instances for direct tools. Use workbenches for grouped integration surfaces such as MCP; do not set both `tools` and `workbench` on the same assistant.

```python
async def lookup_order(order_id: str) -> str:
    return f"order {order_id}: shipped"

assistant = AssistantAgent(
    "support_assistant",
    model_client=model_client,
    tools=[lookup_order],
    reflect_on_tool_use=True,
    max_tool_iterations=2,
)
```

Choose tool result behavior deliberately:
- `reflect_on_tool_use=False`: final response is usually a `ToolCallSummaryMessage` using `tool_call_summary_format`.
- `reflect_on_tool_use=True`: the assistant performs another model call to turn tool outputs into a natural final answer.
- `output_content_type=SomePydanticModel`: structured final responses are enabled; test serialization separately.

## Bounded Round Robin Team

Use `RoundRobinGroupChat` for fixed-turn collaboration and nested teams. Always bound it.

```python
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat

termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(8)
team = RoundRobinGroupChat(
    [planner, implementer, reviewer],
    termination_condition=termination,
    max_turns=8,
)
result = await team.run(task="Draft a migration checklist and stop with TERMINATE.")
```

Design notes:
- `max_turns` is a hard team-level guard; semantic termination is still useful for normal completion.
- A `Team` can be a participant in `RoundRobinGroupChat`, but nested teams should have their own bounds.
- Use `custom_message_types` if custom agents emit non-standard message classes.

## Selector Team

Use `SelectorGroupChat` when a coordinator should choose the next speaker from shared context.

```python
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination

def candidates(messages):
    return ["planner", "reviewer"]

def selector(messages):
    if len(messages) <= 1:
        return "planner"
    return None  # fall back to model-based selection

team = SelectorGroupChat(
    [planner, coder, reviewer],
    model_client=model_client,
    candidate_func=candidates,
    selector_func=selector,
    allow_repeated_speaker=False,
    termination_condition=MaxMessageTermination(6),
    max_turns=6,
)
```

Selector rules:
- `selector_func` must return `None` or exactly one participant name.
- `candidate_func` must return a non-empty list of valid participant names.
- If neither function selects a single speaker, `model_client` is called with `selector_prompt`.
- If repeated speakers are disallowed, verify the candidate list does not contain only the previous speaker unless a fallback is intended.

## Swarm with Handoffs

Use `Swarm` for localized transfer between assistants. Configure each assistant's `handoffs` and use `HandoffTermination` when control must return to an external user or service.

```python
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import HandoffTermination, MaxMessageTermination
from autogen_agentchat.teams import Swarm

triage = AssistantAgent(
    "triage",
    model_client=model_client,
    handoffs=["refunds", "human"],
    system_message="Route refund issues to refunds and uncertain issues to human.",
)
refunds = AssistantAgent("refunds", model_client=model_client, handoffs=["triage", "human"])
team = Swarm(
    [triage, refunds],
    termination_condition=HandoffTermination("human") | MaxMessageTermination(10),
    max_turns=10,
)
```

Checks:
- The first participant must be able to produce `HandoffMessage`; `AssistantAgent` with `handoffs` satisfies this.
- Handoff target names must match participant names or the external target expected by termination.
- Avoid parallel handoff ambiguity by disabling parallel tool calls in model clients when necessary.

## MagenticOneGroupChat

Use the `MagenticOneGroupChat` team API for existing Magentic-One-style orchestration inside AgentChat.

```python
from autogen_agentchat.teams import MagenticOneGroupChat

team = MagenticOneGroupChat(
    [web_surfer, coder, file_surfer],
    model_client=model_client,
    max_turns=20,
    max_stalls=3,
)
```

Boundaries:
- This team takes `ChatAgent` participants only; do not pass nested teams.
- Browser, file, code executor, and provider details are extension/tooling concerns.
- The separate Magentic-One CLI has different package compatibility constraints; route CLI work to `../../tools-studio-bench/SKILL.md`.

## Streaming UI

Use `Console` or explicit async iteration. `run_stream` is not a coroutine result.

```python
from autogen_agentchat.ui import Console

await Console(team.run_stream(task="Investigate and report."))
```

Manual stream handling:

```python
async for event in team.run_stream(task="Investigate and report."):
    if hasattr(event, "to_text"):
        print(event.to_text())
    else:
        print(type(event).__name__)
```

## No-Provider Testing

Before touching credentials, test orchestration with no-provider components:
- Constructor and signature checks using `scripts/agentchat_smoke.py --mode signatures`.
- `BaseChatAgent` echo/stub participants for `RoundRobinGroupChat` and `TeamTool` wiring.
- Replay/mock model clients for `AssistantAgent` and selector behavior when available.
- `MaxMessageTermination` as the default safety bound in synthetic tests.
