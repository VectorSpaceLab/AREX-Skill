# Session Workflows

## Choose Session Memory Or Server-Managed Continuation

Use this decision before writing code:

| If the user needs... | Choose | Why |
| --- | --- | --- |
| App-owned local or database history | `session=SQLiteSession(...)` or another `Session` backend | The SDK retrieves history before each run and persists new turn items after each run. |
| OpenAI-hosted response chaining with only deltas sent | `previous_response_id` or `auto_previous_response_id=True` | The OpenAI Responses API tracks prior response state server-side. |
| A stored OpenAI conversation object | `conversation_id` runner parameter, or `OpenAIConversationsSession` as a session backend | The runner parameter is server-managed continuation; `OpenAIConversationsSession` is a `Session` implementation backed by the Conversations API. Do not combine either session object with runner continuation parameters. |
| Provider-agnostic durable memory | A `Session` backend | Non-OpenAI providers cannot write OpenAI server-side conversation state. |

The runner rejects `session=` combined with `conversation_id`, `previous_response_id`, or `auto_previous_response_id` with `UserError: Session persistence cannot be combined with conversation_id, previous_response_id, or auto_previous_response_id.`

## Quickstart With SQLiteSession

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Reply concisely.")
session = SQLiteSession("thread-123", "conversation_history.db")

first = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
second = await Runner.run(agent, "What state is it in?", session=session)
```

What happens internally:

1. Before the run, the runner calls `session.get_items(...)` and prepends stored history to new input.
2. After the run, the runner persists only new turn items with `session.add_items(...)`.
3. The next run with the same session ID/backend sees the prior conversation.

## Limit Retrieved History

Use `SessionSettings(limit=N)` when a run should read only the latest N stored items while still preserving new turn persistence.

```python
from agents import RunConfig, SessionSettings

result = await Runner.run(
    agent,
    "Continue from recent context only.",
    session=session,
    run_config=RunConfig(session_settings=SessionSettings(limit=50)),
)
```

Important semantics:

- `limit=None` reads all available history.
- `limit=0` reads no history but still persists the new turn.
- Per-run `RunConfig.session_settings` overrides non-`None` defaults from the session instance.
- Limiting retrieval does not delete older stored items.

## Customize History Merge Without Duplicate Saves

Use `RunConfig.session_input_callback` when the model input needs custom pruning, reordering, or filtering. The callback receives copies of `history` and `new_input` and returns the final list for the model call.

```python
from agents import RunConfig


def keep_recent_history(history, new_input):
    return history[-10:] + new_input

result = await Runner.run(
    agent,
    "Use recent context only.",
    session=session,
    run_config=RunConfig(session_input_callback=keep_recent_history),
)
```

The SDK still persists only items belonging to the new turn; filtered or reordered history is not saved again as fresh input.

## Correct The Last Turn With pop_item

Use `pop_item()` to remove the latest item when the user corrects a prompt or the assistant response should be discarded.

```python
await session.pop_item()  # usually assistant response
await session.pop_item()  # usually user message

result = await Runner.run(agent, "Corrected question", session=session)
```

Check for `None` when the session may be empty.

## Direct Memory Operations

```python
items = await session.get_items()
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"},
])
latest = await session.pop_item()
await session.clear_session()
```

Prefer letting `Runner` handle persistence during normal agent runs. Use direct operations for migrations, corrections, tests, or administrative cleanup.

## Resume Interrupted Runs With The Same Session

If a run pauses for human approval or another interruption, convert the result to `RunState`, approve/reject as needed, and resume with the same session object or a new object pointing at the same backing store.

```python
result = await Runner.run(agent, "Delete stale files after approval.", session=session)

if result.interruptions:
    state = result.to_state()
    for interruption in result.interruptions:
        state.approve(interruption)
    result = await Runner.run(agent, state, session=session)
```

For server-managed continuation, resumed `RunState` carries conversation settings. Do not add `session=` to a state that was created with `conversation_id`, `previous_response_id`, or `auto_previous_response_id`.

## OpenAI Server-Managed Continuation

Use `previous_response_id` when an OpenAI Responses run should continue from a known prior response without sending full history again.

```python
first = await Runner.run(agent, "Start the approval flow.")
second = await Runner.run(
    agent,
    "Continue with the next step.",
    previous_response_id=first.last_response_id,
)
```

Use `auto_previous_response_id=True` when a multi-turn run should automatically chain Responses API calls inside the run. The first model call has no previous response ID; later calls use the latest ID returned by the provider.

Use `conversation_id` when OpenAI Conversations should read/write the conversation object for the run. This is OpenAI-specific; prefer SDK sessions for provider-agnostic memory.

## OpenAIConversationsSession

`OpenAIConversationsSession` implements the SDK `Session` protocol using the OpenAI Conversations API. It can lazily create a conversation, or resume one with `conversation_id=`.

```python
from agents import OpenAIConversationsSession

session = OpenAIConversationsSession(conversation_id="conv_123")
result = await Runner.run(agent, "Continue this stored conversation.", session=session)
```

Because it is passed through `session=`, do not also pass runner-level `conversation_id`, `previous_response_id`, or `auto_previous_response_id`.

## Compaction

Use `OpenAIResponsesCompactionSession` when SDK-managed session history grows too large and should be compacted through `responses.compact`.

```python
from agents import SQLiteSession
from agents.memory import OpenAIResponsesCompactionSession

underlying = SQLiteSession("thread-123", "conversation_history.db")
session = OpenAIResponsesCompactionSession(
    session_id="thread-123",
    underlying_session=underlying,
)

result = await Runner.run(agent, "Continue the long conversation.", session=session)
```

Key rules:

- It wraps another `Session`, but not `OpenAIConversationsSession`.
- The default trigger compacts after enough non-user, non-compaction candidate items accumulate.
- `compaction_mode="auto"` chooses between `previous_response_id` and `input` based on available response state.
- Use `compaction_mode="input"` when the session contents should be the source of truth or response IDs are unavailable.
- Use `should_trigger_compaction=lambda _: False` and `await session.run_compaction({"force": True})` when compaction should happen during idle time instead of at the end of a run.

## Encrypted Sessions

Use `EncryptedSession` as a wrapper around another backend when conversation items need encryption and optional expiration.

```python
from agents import SQLiteSession
from agents.extensions.memory import EncryptedSession

underlying = SQLiteSession("user-123", "conversation_history.db")
session = EncryptedSession(
    session_id="user-123",
    underlying_session=underlying,
    encryption_key="application-managed-secret",
    ttl=3600,
)
```

Use a stable application-managed key. If the key changes, existing encrypted items cannot be decrypted. If `ttl` expires, old items are silently skipped during retrieval.
