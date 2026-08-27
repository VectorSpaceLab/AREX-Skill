# Chainlit and UI integration

This reference covers Langroid's Chainlit callback layer and UI-facing integration patterns. It does not cover RAG ingestion or provider/model setup; route those to the appropriate sibling sub-skill from `SKILL.md`.

## What Langroid adds to Chainlit

Langroid provides callback adapters that connect `ChatAgent` and `Task` events to Chainlit messages and steps:

```python
import chainlit as cl
import langroid as lr
from langroid.agent.callbacks.chainlit import (
    ChainlitCallbackConfig,
    add_image,
    add_instructions,
    get_text_files,
)
```

The callback classes are also exported from `langroid` as `lr.ChainlitAgentCallbacks` and `lr.ChainlitTaskCallbacks`.

- `ChainlitAgentCallbacks(agent, config=...)` injects callbacks into one agent.
- `ChainlitTaskCallbacks(task, config=...)` injects callbacks into the task's agent and recursively into sub-task agents.
- `ChainlitCallbackConfig(user_has_agent_name=True, show_subtask_response=True)` controls user labels and whether sub-task responses appear as separate steps.
- `add_instructions()`, `add_image()`, and `get_text_files()` are UI helpers for instructions, image elements, and uploaded text-like files.

The Chainlit callback module is optional. If `chainlit` is not installed, importing the callback module raises a Langroid import error indicating the missing `chainlit` dependency.

## Minimal task-backed app shape

Run the Python app through the Chainlit launcher. The app itself should define handlers; it should not launch Chainlit from inside the handler.

```python
import chainlit as cl
import langroid as lr


@cl.on_chat_start
async def on_chat_start() -> None:
    agent = lr.ChatAgent(
        lr.ChatAgentConfig(
            name="assistant",
            system_message="Answer directly unless a tool is useful.",
        )
    )
    task = lr.Task(agent, interactive=True)
    lr.ChainlitTaskCallbacks(task)
    cl.user_session.set("task", task)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    task = cl.user_session.get("task")
    if task is None:
        await cl.Message(content="Session was not initialized.").send()
        return
    await task.run_async(message.content)
```

Use `Task.run_async()` or agent async methods in Chainlit handlers. Do not call synchronous wrappers that create their own event loop from inside Chainlit callbacks.

## Agent-only app shape

Use direct agent callbacks when you are not using a task loop:

```python
@cl.on_chat_start
async def on_chat_start() -> None:
    agent = lr.ChatAgent(lr.ChatAgentConfig(name="direct-agent"))
    lr.ChainlitAgentCallbacks(agent)
    cl.user_session.set("agent", agent)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent = cl.user_session.get("agent")
    response = await agent.llm_response_async(message.content)
    await agent.agent_response_async(response)
```

For tool-using workflows, a task is usually easier because the task loop manages LLM/tool/agent turns.

## Chainlit with MCP tools

Create MCP tools inside `on_chat_start()` using async helpers:

```python
import os
from fastmcp.client.transports import SSETransport
from langroid.agent.tools.mcp import get_tools_async


@cl.on_chat_start
async def on_chat_start() -> None:
    transport = SSETransport(url=os.environ["MCP_SSE_URL"])
    tools = await get_tools_async(transport)

    agent = lr.ChatAgent(lr.ChatAgentConfig(name="mcp-agent"))
    agent.enable_message(tools)
    task = lr.Task(agent, interactive=False)
    lr.ChainlitTaskCallbacks(task)
    cl.user_session.set("task", task)
```

For stdio MCP servers, construct the transport inside the async handler or pass a factory to Langroid's MCP helper. Avoid module-level subprocess transport creation in a Chainlit app.

## Streaming and callback behavior

When Chainlit callbacks are injected into an agent with an LLM, Langroid sets `agent.llm.config.async_stream_quiet = False` so streamed tokens can appear in the UI. If a task seems silent in Chainlit, check whether callbacks were injected after task creation and before `run_async()`.

The callback layer displays:

- LLM responses, including tool-call JSON when present.
- Agent/tool-handler responses.
- User prompts via Chainlit ask messages when Langroid requests input.
- Long-running start responses as spinner-like Chainlit messages.
- Nested sub-task responses when `show_subtask_response=True`.
- Reasoning content when the LLM response object supplies a reasoning field.

## UI helpers

### Instructions

```python
await add_instructions(
    title="Instructions",
    content="Ask a question. The assistant may use tools when useful.",
    display="inline",
)
```

### Image elements

```python
await add_image(path="public/logo.png", name="Logo", display="inline")
```

Use paths served by the Chainlit app. Keep app assets within the app's intended public/static layout.

### Uploaded text-like files

```python
@cl.on_message
async def on_message(message: cl.Message) -> None:
    files = await get_text_files(message, extensions=[".txt", ".md", ".pdf"])
```

Use this only to collect uploaded file paths. Route document ingestion and retrieval behavior to the retrieval sub-skill.

## Local server and help-only checks

Before debugging Langroid itself, verify the UI boundary:

```bash
python -c "import chainlit"
chainlit --help
```

These checks do not start a Chainlit app. Start the UI separately with the Chainlit launcher when you intentionally want an interactive server.

## Common boundaries

- Chainlit code runs inside an active Chainlit event loop; avoid `asyncio.run()` inside handlers.
- Callback injection is per agent/task instance. Recreate or reinject callbacks when recreating the task in session state.
- Chainlit installation and server launch are optional UI concerns. Core Langroid tools can be tested without Chainlit.
- External MCP/search service credentials should be checked before UI startup so failures appear as clear setup errors rather than silent UI stalls.
