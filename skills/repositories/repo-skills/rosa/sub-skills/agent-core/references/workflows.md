# ROSA agent-core workflows

The snippets below are safe documentation skeletons. They do not contact a
model, require credentials, name a live ROS entity, launch Docker/TurtleSim, or
assume a ROS graph is running. Replace `configured_tool_calling_model()` with a
provider model prepared according to [llm-configuration.md](llm-configuration.md).

## Install and import

```bash
python -m pip install jpl-rosa
```

For optional providers, install the relevant extra before importing its model
class, for example `python -m pip install 'jpl-rosa[ollama]'`. Installation
provides the Python package and LangChain dependencies; it does **not** install
ROS 1/ROS 2 middleware, source a ROS environment, or start a ROS graph.

```python
import rosa
from rosa import ChatModel, ROSA, RobotSystemPrompts

assert {"ROSA", "RobotSystemPrompts", "ChatModel"}.issubset(rosa.__all__)
```

This import check is independent of credentials and a model. Construction is
not: `ROSA(ros_version=1, ...)` needs the ROS 1 Python environment, while
`ROSA(ros_version=2, ...)` needs the ROS 2 Python/runtime prerequisites.

## Construct a non-streaming agent

Prepare a tool-calling model without placing its key in source or prompts, then
select the ROS family explicitly:

```python
from rosa import ROSA

llm = configured_tool_calling_model(streaming=False)  # provider-specific
agent = ROSA(
    ros_version=2,
    llm=llm,
    streaming=False,
    accumulate_chat_history=True,
    max_iterations=20,
)
```

The constructor loads the selected ROS tool family and can fail before any
query if its middleware is absent. It is therefore valid to test the import
step on a machine without ROS, but not to claim that the agent is constructed
there.

## Synchronous invocation

```python
answer = agent.invoke("Answer using the available read-only ROS information.")
if answer.startswith("An error occurred:"):
    # Treat this as a returned execution failure, not as a successful answer.
    inspect_provider_or_tool_diagnostics(answer)
else:
    print(answer)
```

`invoke()` returns a string on success. Ordinary exceptions are converted to an
error string and the failed query is not added to history. `KeyboardInterrupt`
is deliberately re-raised so an outer application can stop cleanly.

## Consume asynchronous events

Use a streaming-capable model and construct ROSA with `streaming=True` (the
constructor default):

```python
async def run_stream(agent, query):
    parts = []
    async for event in agent.astream(query):
        kind = event["type"]
        if kind == "token":
            parts.append(event["content"])
            render_token(event["content"])
        elif kind == "tool_start":
            observe_tool_start(event["name"], event.get("input"))
        elif kind == "tool_end":
            observe_tool_end(event["name"], event.get("output"))
        elif kind == "final":
            render_final(event["content"])
        elif kind == "error":
            report_stream_error(event["content"])
    return "".join(parts)
```

Events are emitted in the order observed from LangChain's executor. Do not
assume a token event for every provider chunk or a final event after an error.
Use the ROS-family route to choose safe, discovery-first queries and execute
one tool action at a time.

## Reset or disable history

```python
old_messages = list(agent.chat_history)
agent.clear_chat()
assert agent.chat_history == []

stateless_agent = ROSA(
    ros_version=2,
    llm=llm,
    streaming=False,
    accumulate_chat_history=False,
)
```

`clear_chat()` affects only this object. With accumulation disabled, the
executor still receives the current (normally empty) list, but successful
turns are not appended. Streaming records a turn only when non-empty output was
accumulated.

## Intermediate steps, verbosity, and bounded loops

```python
trace_agent = ROSA(
    ros_version=2,
    llm=llm,
    streaming=False,
    verbose=True,
    max_iterations=10,
    return_intermediate_steps=True,
)
answer = trace_agent.invoke("Use available tools to answer a bounded question.")
```

`verbose` delegates display to `AgentExecutor`. `return_intermediate_steps`
requests executor traces and may increase memory use, but ROSA's public
`invoke()` still returns only the output string. `max_iterations` limits the
agent executor; parser failures are handled by the executor and can consume
iterations, so choose a finite value appropriate to the task.

For custom tools, packages, blacklists, and robot-specific prompts, follow
[tool-customization](../../tool-customization/SKILL.md) rather than embedding
extension implementation in this lifecycle route.
