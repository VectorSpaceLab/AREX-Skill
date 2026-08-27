# Agent Core API Reference

## Core import surface

```python
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import ChatHistory, BaseChatHistory, SystemPromptGenerator, BaseDynamicContextProvider
from atomic_agents.utils import TokenCounter, TokenCountResult, format_tool_message
from atomic_agents.base.multimodal import VideoURL
```

## AtomicAgent

`AtomicAgent[InputSchema, OutputSchema](config=AgentConfig(...))`

Key methods and properties:

| Member | Purpose |
| --- | --- |
| `run(user_input=None)` | Sync completion call for sync Instructor clients. |
| `run_stream(user_input=None)` | Sync streaming generator that yields partial structured responses. |
| `run_async(user_input=None)` | Async completion call for `AsyncInstructor` clients. |
| `run_async_stream(user_input=None)` | Async streaming generator for `AsyncInstructor` clients. |
| `reset_history()` | Restore the initial history snapshot. |
| `add_tool_result(content)` | Add a tool result / mid-conversation injection with the correct backend-aware role. |
| `get_context_token_count()` | Count system prompt + history + schema/tool overhead. |
| `get_context_provider(name)` / `register_context_provider()` / `unregister_context_provider()` | Manage dynamic context providers. |
| `register_hook()` / `unregister_hook()` / `clear_hooks()` / `enable_hooks()` / `disable_hooks()` | Manage Instructor hook handlers. |

Important runtime facts:

- The agent stores the type parameters on the class at construction time so subclassing and direct instantiation both work.
- `tool_result_role` defaults to `user` for Gemini-style backends (`assistant_role='model'`) and to `system` otherwise.
- `mode` defaults to `Mode.TOOLS`.
- `model_api_parameters` are passed through to Instructor completion calls, and `strict` defaults to `None` unless overridden.
- `max_context_tokens` trims whole turns, not individual messages.

## AgentConfig

`AgentConfig` is a Pydantic model with these fields:

| Field | Meaning |
| --- | --- |
| `client` | An `instructor.Instructor` or `AsyncInstructor` client. |
| `model` | Model name passed to the provider. Default: `gpt-5-mini`. |
| `history` | A `BaseChatHistory` implementation. Defaults to `ChatHistory`. |
| `system_prompt_generator` | A `BaseSystemPromptGenerator`. Defaults to `SystemPromptGenerator`. |
| `system_role` | The role used for the initial system prompt. Default: `system`. |
| `assistant_role` | The assistant role used when storing responses. Default: `assistant`. |
| `tool_result_role` | Mid-conversation tool-result role override; auto-detected if omitted. |
| `mode` | Instructor mode. Default: `Mode.TOOLS`. |
| `model_api_parameters` | Additional provider parameters such as temperature or max tokens. |
| `max_context_tokens` | Optional context-window cap for turn trimming. |

## Schema base classes

### BaseIOSchema

- Inherits from `pydantic.BaseModel`.
- Requires a non-empty docstring unless it is an Instructor-generated schema.
- Serializes cleanly with `model_json_schema()` and rich JSON rendering.

### BasicChatInputSchema / BasicChatOutputSchema

- The built-in minimal chat schemas.
- Both inherit from `BaseIOSchema`.
- `BasicChatInputSchema.chat_message` is the canonical user input field.
- `BasicChatOutputSchema.chat_message` is the canonical assistant output field.

## Memory and prompt classes

### ChatHistory

Built-in in-memory `BaseChatHistory` implementation with:

- `initialize_turn()`
- `add_message(role, content)`
- `get_history()`
- `get_current_turn_id()`
- `delete_turn_id(turn_id)`
- `get_message_count()`
- `dump()` / `load()` / `copy()`

Important behavior:

- `get_history()` emits JSON strings and multimodal content parts in the format expected by Instructor.
- Nested multimodal content is extracted recursively.
- `copy()` preserves `max_messages` and current turn state.

### BaseChatHistory

The abstract contract that custom backends must satisfy. Implement `copy()` carefully so `reset_history()` does not drop backend state.

### SystemPromptGenerator

Structured prompt builder with `background`, `steps`, `output_instructions`, and `context_providers` sections. It always appends the standard JSON-schema and context-use instructions.

### BaseDynamicContextProvider

Abstract base for dynamic context injection. Implement `get_info()` and keep it cheap because it may run on every agent call.

## Token counting and multimodal helpers

### TokenCounter / TokenCountResult

- `count_messages(model, messages, tools=None)`
- `count_text(model, text)`
- `get_max_tokens(model)`
- `count_context(model, system_messages, history_messages, tools=None)`

`TokenCountResult` fields: `total`, `system_prompt`, `history`, `tools`, `model`, `max_tokens`, `utilization`.

### VideoURL

A simple model that converts to an OpenAI-compatible `video_url` content part through `to_openai()`.

## Related docs

- Use `workflows.md` for recipes.
- Use `troubleshooting.md` for common failure modes.
