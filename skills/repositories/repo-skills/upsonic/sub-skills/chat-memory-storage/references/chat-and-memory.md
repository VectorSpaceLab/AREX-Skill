# Chat and Memory Reference

## Verified shapes

| Surface | Verified behavior |
| --- | --- |
| `Chat(session_id, user_id, agent, *, storage=None, full_session_memory=True, summary_memory=False, user_analysis_memory=False, ...)` | Binds an Agent to Memory and Storage and keeps session state in one place. |
| `Memory(storage, session_id=None, user_id=None, full_session_memory=False, summary_memory=False, user_analysis_memory=False, ...)` | Owns the persistence strategy for a session and its user-linked memory. |
| `Chat.invoke(input_data, *, context=None, stream=False, events=False, return_run_output=False, **kwargs)` | Primary invocation path when a chat session should persist history and state. |
| `Chat.get_raw_messages()` / `Chat.reset_session()` / `Chat.reopen()` / `Chat.close()` | Session inspection and lifecycle control methods. |

## Typical workflow

```python
from upsonic import Agent, Chat

agent = Agent(model="openai/gpt-4o")
chat = Chat(session_id="demo", user_id="user-1", agent=agent)
result = chat.invoke("Hello, keep context across turns")
```

## What to remember

- Use `Chat` when the user wants a conversational session, not a single stateless run.
- Use `Memory` directly when you only need the persistence layer.
- Keep session ids stable if you want the same conversation to reload.
- Route RAG document storage and retrieval to knowledge-rag, not here.
