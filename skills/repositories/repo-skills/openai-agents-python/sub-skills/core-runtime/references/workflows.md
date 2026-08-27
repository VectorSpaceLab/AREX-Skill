# Core Runtime Workflows

Use these recipes as safe patterns for future agents. They do not require original repository files at runtime.

## Define a Plain Agent

```python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="Answer concisely and ask a clarifying question when requirements are ambiguous.",
)
```

Decision checklist:

- Set `instructions` for ordinary system behavior.
- Set `output_type` when the caller needs structured final output.
- Set `model` only when this agent should differ from the run-wide default.
- Keep tools, handoffs, guardrails, MCP, and sandbox decisions in their sibling sub-skills.

## Run Asynchronously

Use this inside async applications, services, notebooks with an active loop, and tests:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be brief.")
result = await Runner.run(agent, "Write a haiku about recursion.")
print(result.final_output)
```

After completion:

- Use `result.final_output` for the final answer.
- Use `result.new_items` for rich audit/UI metadata.
- Use `result.to_input_list()` only when manually carrying local conversation history.
- Use `result.last_agent` if a handoff changed which agent should handle the next user turn.

## Run Synchronously

Use this only in synchronous code with no already-running event loop:

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Be brief.")
result = Runner.run_sync(agent, "Summarize the SDK in one sentence.")
print(result.final_output)
```

If this raises an event-loop error or the caller is inside FastAPI/Jupyter/async code, convert the caller to `await Runner.run(...)` instead.

## Stream Raw Tokens and Semantic Events

```python
from agents import Agent, ItemHelpers, Runner

agent = Agent(name="Assistant", instructions="Use tools when helpful, then answer.")
result = Runner.run_streamed(agent, "Explain recursion with one example.")

async for event in result.stream_events():
    if event.type == "raw_response_event":
        # Inspect event.data for provider-native text deltas or tool-call argument deltas.
        continue
    if event.type == "agent_updated_stream_event":
        print(f"active agent: {event.new_agent.name}")
        continue
    if event.type == "run_item_stream_event":
        if event.item.type == "message_output_item":
            print(ItemHelpers.text_message_output(event.item))
        elif event.name == "tool_called":
            print("tool call emitted")
        elif event.name == "tool_output":
            print("tool output available")

if result.run_loop_exception:
    raise result.run_loop_exception
print(result.final_output)
```

Important rules:

- Keep iterating `stream_events()` until the async iterator exits.
- `final_output`, `interruptions`, `raw_responses`, and session side effects may not be complete until the stream is drained.
- Treat `raw_response_event` as provider-native; use `run_item_stream_event` for stable SDK-level UI milestones.
- `current_agent` can update before completion; `last_agent` is reliable after completion.

## Diagnose Raw Tool Argument Deltas Without Final Output

When raw streaming shows function/tool argument deltas but no final answer:

1. Confirm the stream was fully drained; a tool-call turn often has no final text until after tool execution and a follow-up model call.
2. Look for `run_item_stream_event` with `name="tool_called"` and later `name="tool_output"`.
3. If a tool requires approval, the stream can finish with `result.final_output is None` and pending `result.interruptions`.
4. If `tool_output` is missing, route tool implementation and approval setup to ../tools-handoffs-guardrails/SKILL.md.
5. If `run_loop_exception` is set after draining, raise or log it; early loop failures can otherwise look like silent streams.
6. If `max_turns` is too small, the stream may raise `MaxTurnsExceeded` before a final answer.

This case is common when UI code prints only raw text deltas and ignores semantic events. Tool-call argument deltas are not user-facing final output.

## Cancel Streaming

```python
result = Runner.run_streamed(agent, "Do a long task.")

async for event in result.stream_events():
    if should_stop_now(event):
        result.cancel(mode="after_turn")
```

Use `mode="after_turn"` when you want the current model/tool turn to finish cleanly and preserve session/history side effects. After any cancellation, keep consuming `stream_events()` until it exits. If continuing manually after a graceful cancel, prefer `result.to_input_list(mode="normalized")` with `result.last_agent` rather than appending a fresh user turn to an incomplete tool cycle.

## Handle Max Turns

```python
from agents import MaxTurnsExceeded

try:
    result = await Runner.run(agent, "Complete this complex task.", max_turns=3)
except MaxTurnsExceeded as exc:
    partial_items = exc.run_data.new_items if exc.run_data else []
    raise
```

Guidance:

- A turn is one model invocation plus any tool calls from that invocation.
- Tool/handoff loops can use multiple turns for one user request.
- Set `max_turns=None` only when the surrounding application has its own loop guard.
- Prefer debugging why the loop repeats before simply raising the limit.

## Return a Controlled Fallback for Max Turns

```python
from agents import Agent, RunErrorHandlerInput, RunErrorHandlerResult, Runner


def on_max_turns(_data: RunErrorHandlerInput[None]) -> RunErrorHandlerResult:
    return RunErrorHandlerResult(
        final_output="I could not finish within the turn limit. Please narrow the request.",
        include_in_history=False,
    )

agent = Agent(name="Assistant", instructions="Be concise.")
result = Runner.run_sync(
    agent,
    "Analyze this long transcript.",
    max_turns=3,
    error_handlers={"max_turns": on_max_turns},
)
```

Use `include_in_history=False` when fallback text should not become part of future conversation history.

## Pause, Approve, and Resume a RunState

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="Use approved tools when needed.")
result = await Runner.run(agent, "Perform the sensitive action if appropriate.")

if result.interruptions:
    state = result.to_state()
    for interruption in result.interruptions:
        state.approve(interruption, always_approve=False)
    result = await Runner.run(agent, state)

print(result.final_output)
```

Rules that prevent resume bugs:

- Resume the original top-level agent, not a nested agent that happened to request approval.
- Approve or reject items on the `RunState`, not on the `RunResult`.
- Do not append a new user message when resuming approval; pass the `RunState` itself as `input`.
- The SDK preserves current turn and server-managed IDs inside `RunState`; approval resume should not rerun first-turn input guardrails as a fresh user turn.
- If only some interruptions are resolved, rerunning can continue resolved calls and pause again for unresolved ones.

## Streamed Approval Resume

```python
result = Runner.run_streamed(agent, "Perform the sensitive action if appropriate.")
async for _event in result.stream_events():
    pass

if result.interruptions:
    state = result.to_state()
    for interruption in result.interruptions:
        state.approve(interruption)
    resumed = Runner.run_streamed(agent, state)
    async for _event in resumed.stream_events():
        pass
    result = resumed
```

Never inspect `result.interruptions` or call `to_state()` before the original streamed iterator has finished.

## Persist and Reload a RunState

```python
from agents import RunState

state = result.to_state()
stored = state.to_string()

# Later, with the same compatible top-level agent graph:
state = await RunState.from_string(agent, stored)
for interruption in state.get_interruptions():
    state.reject(interruption, rejection_message="Reviewer denied this action.")
result = await Runner.run(agent, state)
```

For custom context objects, provide matching `context_serializer` and `context_deserializer` or use `context_override` during load. Store an application schema/version marker with long-lived states so old approvals can be resumed by compatible agent definitions.

## Manual Local Conversation Loop

```python
agent = Agent(name="Assistant", instructions="Reply very concisely.")

result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
print(result.final_output)

next_input = result.to_input_list() + [
    {"role": "user", "content": "What state is it in?"},
]
result = await Runner.run(result.last_agent, next_input)
print(result.final_output)
```

Use `to_input_list(mode="normalized")` when a handoff input filter or nested handoff history rewrite changed the canonical continuation history.

## Server-Managed Conversation With previous_response_id

```python
agent = Agent(name="Assistant", instructions="Reply very concisely.")
previous_response_id = None

result = await Runner.run(
    agent,
    "What city is the Golden Gate Bridge in?",
    previous_response_id=previous_response_id,
    auto_previous_response_id=True,
)
previous_response_id = result.last_response_id

result = await Runner.run(
    agent,
    "What state is it in?",
    previous_response_id=previous_response_id,
)
```

Use this only with OpenAI Responses API-compatible model paths. Pass only the new user turn rather than `to_input_list()`.

## Server-Managed Conversation With conversation_id

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()
conversation = await client.conversations.create()

agent = Agent(name="Assistant", instructions="Reply very concisely.")
result = await Runner.run(agent, "Hello", conversation_id=conversation.id)
```

Use `conversation_id` when a named server-side conversation must be shared across workers or services. Do not combine it with `previous_response_id`, `auto_previous_response_id`, or `session` in the same run.

## Local Session at a High Level

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Reply very concisely.")
session = SQLiteSession("conversation_123")

result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
result = await Runner.run(agent, "What state is it in?", session=session)
```

This sub-skill only covers the high-level interaction with `Runner`. Route backend setup, retention, compaction, and custom session stores to ../sessions-memory/SKILL.md.

## Filter Model Input Before Each Call

```python
from agents import Agent, RunConfig, Runner
from agents.run import CallModelData, ModelInputData


def keep_recent_items(data: CallModelData[None]) -> ModelInputData:
    recent = data.model_data.input[-5:]
    return ModelInputData(input=recent, instructions=data.model_data.instructions)

agent = Agent(name="Assistant", instructions="Answer concisely.")
result = Runner.run_sync(
    agent,
    "Explain quines.",
    run_config=RunConfig(call_model_input_filter=keep_recent_items),
)
```

Input-filter checklist:

- Return `ModelInputData`, not a raw list or dict.
- Keep `input` as a list of Responses input items.
- Preserve or deliberately replace `instructions`.
- With sessions, this hook runs after session history is retrieved and merged.
- With server-managed conversation state, returned items are what the tracker marks as sent for that continuation.

## Tool Not Found Recovery

```python
from agents import Agent, RunConfig, Runner

agent = Agent(name="Assistant", instructions="Use only listed tools.")
result = await Runner.run(
    agent,
    "Handle this with available tools.",
    run_config=RunConfig(tool_not_found_behavior="return_error_to_model"),
)
```

Default behavior raises `ModelBehaviorError` for unresolved function tool calls. Opt into `return_error_to_model` only when the model should see an error output and try again. Use `tool_error_formatter` to customize that model-visible text.
