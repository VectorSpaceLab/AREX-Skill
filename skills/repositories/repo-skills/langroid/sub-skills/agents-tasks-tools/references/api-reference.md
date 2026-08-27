# API reference

This file distills the Langroid agent/task/tool surface used by this sub-skill.
Keep it handy when you need to debug a tool path, routing path, termination path,
or deterministic test setup.

## 1. Agent and config surface

### `ChatAgentConfig`

Key fields for this sub-skill:

| Field | Meaning | Default / note |
| --- | --- | --- |
| `use_tools` | Enable Langroid-native tool parsing and prompting | `True` |
| `use_functions_api` | Enable provider-native function/tool calling | `False` |
| `use_tools_api` | Use the newer provider tool-call API when provider tools are enabled | `True` |
| `handle_llm_no_tool` | Fallback when the LLM emits a plain response instead of a tool | `None` |
| `recognize_recipient_in_content` | Parse `TO[...]` or JSON recipient hints in message text | `True` |
| `output_format` | Strict typed output target | `None` |
| `use_output_format` / `handle_output_format` | Control whether the output type is requested and/or handled | `True` |
| `use_tools_on_output_format` | Switch output-format handling to Langroid tools | `True` |
| `enable_orchestration_tool_handling` | Auto-enable orchestration tools such as `DoneTool` | `True` |

Notes:

- For native Langroid tools, keep `use_tools=True` and `use_functions_api=False`.
- For provider tool calling, use `use_tools=False` and `use_functions_api=True`.
- For XML tools, use native tools only.
- `handle_llm_no_tool` is only applied when the message is from the LLM and contains no usable tool.

### `ChatAgent`

The main responder surface is:

- `agent_response`
- `llm_response`
- `user_response`

Important methods:

| Method | Purpose |
| --- | --- |
| `enable_message(message_class, use=True, handle=True, force=False, require_recipient=False, include_defaults=True)` | Register a `ToolMessage` for use and/or handling |
| `disable_message_use(message_class)` | Disable LLM generation of a tool |
| `disable_message_handling(message_class)` | Disable agent handling of a tool |
| `get_tool_messages(msg, all_tools=False)` | Extract recognized tool messages |
| `try_get_tool_messages(msg, all_tools=False)` | Safe version of `get_tool_messages` |
| `set_output_format(type_or_tool)` | Attach a structured output format |
| `agent[type]` | Create a typed/strict copy of the agent |

`enable_message` accepts either one `ToolMessage` subclass, a list of subclasses, or `None`.
The parameters mean:

- `use`: allow the LLM to emit this tool
- `handle`: allow the agent to process this tool
- `force`: force the LLM to prefer this tool
- `require_recipient`: add a required recipient field to the tool
- `include_defaults`: include default-valued fields in schema/instructions

A useful rule:

- `use=True, handle=True` for normal tool round-trips
- `use=False, handle=True` for handler-only tools or sub-agent-only tools
- `use=True, handle=False` for tools the LLM may emit but the current agent should not handle

### `ToolMessage`

Core fields and helpers:

- `request`: tool name / handler name
- `purpose`: natural-language description sent to the model
- `examples()`: optional few-shot examples
- `usage_examples()`: formatted examples for prompting
- `handle()` / `handle_async()`: stateless handler hooks
- `response()` / `response_async()`: alternate handler hooks that can use the current `ChatDocument`
- `_allow_llm_use`: gate that blocks LLM generation
- `require_recipient()`: returns a variant with a required recipient field

If a tool defines `handle` or `response`, `enable_message(..., handle=True)` can inject the handler into the agent automatically.

### `XMLToolMessage`

Use this for XML-formatted tools, especially when the payload contains code or other text that should be preserved exactly.

Rules of thumb:

- mark verbatim fields so whitespace and code stay unchanged
- keep `use_tools=True`
- keep `use_functions_api=False`

## 2. Routing and orchestration tools

### Orchestration tools

| Tool | Use case |
| --- | --- |
| `DoneTool` | End the current task with a string result |
| `AgentDoneTool` | End the current task with content and optional nested tools |
| `ResultTool` | Return arbitrary structured data and end the current task |
| `FinalResultTool` | Return arbitrary structured data and end the current task and all parents |
| `PassTool` | Pass the current message onward |
| `DonePassTool` | Pass the message and end the task |
| `ForwardTool` | Forward to a specific recipient |
| `SendTool` / `AgentSendTool` | Explicit message sending variants |

`ResultTool` and `FinalResultTool` are the preferred choices when you want a structured payload to survive the round trip.

### `RecipientTool`

Use `RecipientTool` when the LLM must name the intended recipient explicitly.

Important pieces:

- request name: `recipient_message`
- required fields: `intended_recipient`, `content`
- `create(recipients, default="")` builds a restricted recipient variant
- missing recipients trigger the helper `AddRecipientTool`

Text-based recipient parsing is controlled by `ChatAgentConfig.recognize_recipient_in_content`.

## 3. Task and termination surface

### `TaskConfig`

Key fields for this sub-skill:

| Field | Meaning | Default / note |
| --- | --- | --- |
| `done_sequences` | Ordered event patterns that end the task | `None` |
| `done_if_tool` | End when a tool is generated | `False` |
| `single_round` | End after one valid exchange | `False` |
| `recognize_string_signals` | Parse `DONE`, `PASS`, `DONE_PASS`, and similar text signals | `True` |
| `allow_subtask_multi_oai_tools` | Allow multiple OpenAI tool calls in a sub-task | `True` |
| `enable_loggers` / `enable_html_logging` | Logging controls | `True` |

`done_sequences` can be either `DoneSequence` objects or DSL strings. The DSL tokens are:

- `T` any tool
- `T[name]` specific tool by request name
- `T[ToolClass]` specific tool by class name
- `A` agent response
- `L` LLM response
- `U` user response
- `N` no response
- `C[regex]` content match

### `Task`

A `Task` wraps an agent and orchestrates the responder loop.
Useful methods and behaviors:

- `run()` and `run_async()` are the main entry points
- `add_sub_task()` composes one task inside another
- `Task.run()` and the agent responder methods share a compatible signature
- `TaskTool` uses the same idea to run a child task from inside a tool handler

### `TaskTool`

`TaskTool` spawns a non-interactive sub-agent. Key fields:

- `system_message`
- `prompt`
- `tools`
- optional `model`
- optional `max_iterations`
- optional `agent_name`

Behavior to remember:

- the sub-agent always gets `DoneTool`
- `tools=["ALL"]` means all parent-known allowed tools
- `tools=["NONE"]` disables extra tools
- delegated tools must already be known to the parent agent

## 4. Structured output

Two common patterns are supported:

1. `agent[OutputType]` for a strict typed copy
2. `set_output_format(OutputType)` for explicit output-format control

A standard pattern is:

```python
response = agent[OutputType].llm_response_forget(prompt)
value = agent.from_ChatDocument(response, OutputType)
```

Use this when you want a typed value instead of a conversational reply.

## 5. MockLM

`MockLMConfig` is the deterministic test model.
It does **not** use a `response` field.
The fields you should expect are:

- `response_dict`
- `response_fn`
- `response_fn_async`
- `default_response`

Response order:

- sync: `response_dict` → `response_fn` → `default_response`
- async: `response_dict` → `response_fn_async` → `response_fn` → `default_response`

Use `MockLM` whenever a test must avoid provider keys or network calls.

## 6. Batch helpers

The batch helpers in `langroid.agent.batch` are:

- `run_batch_tasks`
- `run_batch_task_gen`
- `run_batch_agent_method`
- `llm_response_batch`
- `agent_response_batch`
- `run_batch_function`

Important semantics:

- `stop_on_first_result=True` returns the first non-`None` result after `output_map`
- later tasks are cancelled once a valid result appears
- `sequential=True` keeps the execution ordered and one-at-a-time
- `batch_size` processes fixed-size chunks
- `handle_exceptions` can return `None`, raise, or return the exception object

## 7. Quick checks

If a workflow is still ambiguous, ask:

- Is this a tool path, a routing path, a termination path, or a typed-output path?
- Does the model need native tools, provider tools, or XML tools?
- Should the task stop on a tool, a sequence, a done tool, or a typed return?
