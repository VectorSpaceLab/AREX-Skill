# ROSA agent-core API reference

These contracts are verified against distribution `jpl-rosa` 1.0.10. Python
support is `>=3.9,<4`. The public import is `rosa`.

## Public exports

```python
from rosa import ROSA, RobotSystemPrompts, ChatModel
```

`ChatModel` is the exported model type alias. At runtime the package accepts a
`langchain_core.language_models.BaseChatModel`; the tested provider classes are
OpenAI, Azure OpenAI, Anthropic, and Ollama variants. The model must support
LangChain tool calling.

## Constructor

```python
ROSA(
    ros_version: Literal[1, 2],
    llm: ChatModel,
    tools: Optional[list] = None,
    tool_packages: Optional[list] = None,
    prompts: Optional[RobotSystemPrompts] = None,
    verbose: bool = False,
    blacklist: Optional[list] = None,
    accumulate_chat_history: bool = True,
    show_token_usage: bool = False,
    streaming: bool = True,
    max_iterations: int = 100,
    return_intermediate_steps: bool = False,
)
```

The constructor creates the default deterministic tools and the selected ROS
family tools, adds optional tools/packages, builds a tool-calling agent, and
creates an `AgentExecutor`. Consequently, `import rosa` can succeed without
ROS middleware while `ROSA(...)` can fail if the selected ROS modules/runtime
are unavailable. Package installation itself does not install that middleware.

| Argument | Verified default/contract | Interaction |
|---|---|---|
| `ros_version` | `1` or `2` | Selects the ROS tool family. Other values fail during tool construction with `Invalid ROS version. Must be either 1 or 2.` |
| `llm` | required `ChatModel` | Must provide tool-calling behavior; the instance is configured with the requested streaming flag. |
| `tools` | `None` | Optional LangChain tool list; detailed extension rules are in [tool-customization](../../tool-customization/SKILL.md). |
| `tool_packages` | `None` | Optional packages containing LangChain tools; see [tool-customization](../../tool-customization/SKILL.md). |
| `prompts` | `None` | Optional `RobotSystemPrompts` appended as a robot-specific system message. |
| `verbose` | `False` | Passed to `AgentExecutor`; enables verbose executor output when true. |
| `blacklist` | `None` | Passed to ROS/tool assembly; detailed semantics belong to [tool-customization](../../tool-customization/SKILL.md). |
| `accumulate_chat_history` | `True` | Successful calls append a human and AI message pair; false keeps calls stateless. |
| `show_token_usage` | `False` | Only effective for non-streaming `ChatOpenAI` or `AzureChatOpenAI`; otherwise disabled. |
| `streaming` | `True` | Controls model/executor streaming and whether `astream()` is usable. It forces token display off. |
| `max_iterations` | `100` | Passed to `AgentExecutor`; tool-call/parser loops are bounded by this executor limit. |
| `return_intermediate_steps` | `False` | Passed to `AgentExecutor`; may increase memory use, but `invoke()` still returns only `result["output"]`. |

## Methods and property

```python
agent.invoke(query: str) -> str
agent.astream(query: str) -> AsyncIterable[Dict[str, Any]]
agent.clear_chat()
agent.chat_history  # readable list of LangChain messages
```

### `invoke(query)`

- Calls the executor with `input=query` and the current `chat_history`.
- On success, records `HumanMessage(query)` and `AIMessage(output)` when
  accumulation is enabled, then returns the output string.
- On an ordinary exception, returns exactly `f"An error occurred: {str(e)}"` and
  does not record that failed call.
- Re-raises `KeyboardInterrupt` instead of converting it to an error string.
- If token display is enabled and supported, prints prompt tokens, completion
  tokens, and total USD cost after the executor call.

### `astream(query)`

`astream` is an asynchronous iterable, not a coroutine returning one final
string. If the instance was created with `streaming=False`, iteration raises:

```text
ValueError: Streaming is not enabled. Use 'invoke' method instead or initialize ROSA with streaming=True.
```

With streaming enabled, executor v2 events are mapped to these dictionaries:

| `type` | Additional keys | Meaning |
|---|---|---|
| `token` | `content` | Non-empty chat-model stream chunk content. |
| `tool_start` | `name`, `input` | A tool execution began; input may be absent/`None`. |
| `tool_end` | `name`, `output` | A tool execution ended; output may be absent/`None`. |
| `final` | `content` | The `Agent` chain supplied its final output. |
| `error` | `content` | Streaming caught an ordinary exception, or converted an interrupt to an interruption error event. |

The final output is recorded as an AI message with the query when a non-empty
final output was observed. Ordinary streaming failures yield an `error` event
rather than raising through the async iterator. `KeyboardInterrupt` is also
converted by this method to `{"type": "error", "content": "Operation interrupted by user"}`.

### `chat_history` and `clear_chat()`

`chat_history` is the readable list passed to the prompt's `chat_history`
placeholder. `clear_chat()` replaces it with an empty list. History is not
persisted outside the object and is not recorded for an ordinary failed
`invoke()`; streaming records only after output has been accumulated.

## Prompt contract

`RobotSystemPrompts` accepts these optional fields:

```python
RobotSystemPrompts(
    embodiment_and_persona=None,
    about_your_operators=None,
    critical_instructions=None,
    constraints_and_guardrails=None,
    about_your_environment=None,
    about_your_capabilities=None,
    nuance_and_assumptions=None,
    mission_and_objectives=None,
    environment_variables=None,
)
```

`as_message() -> tuple` returns `("system", str(self))`. Its string form
includes non-empty public string fields with title-cased labels; the optional
dictionary `environment_variables` is accepted and stored but is not rendered
by that string conversion. Use [tool-customization](../../tool-customization/SKILL.md)
for prompt composition and safety guidance.
