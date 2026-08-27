# API reference

This reference records the public surface that the `llm-providers` sub-skill is
allowed to use and explain.

## Public entry points

```python
from giskard.llm import (
    LLMClient,
    configure,
    reset,
    acompletion,
    aembedding,
    aresponse,
    should_retry,
)
```

### `LLMClient`

```python
LLMClient() -> None
LLMClient.configure(name: str, provider: str | None = None, **kwargs) -> None
LLMClient.configure_from_dict(config: dict[str, dict[str, Any]]) -> None
LLMClient.acompletion(model: str, messages, *, tools=None, **params)
LLMClient.aembedding(model: str, input: list[str], **params)
LLMClient.aresponse(model: str, input, *, instructions=None, previous_id=None, tools=None, **params)
```

Behavioral notes:

- `LLMClient` stores named aliases and creates provider instances lazily.
- `configure(name, provider=None, **kwargs)` stores an alias. If `provider` is
  omitted, the alias name is also treated as the provider type.
- `reset()` clears the module-level default client configuration and cached
  provider instances.
- Alias configuration may use deferred environment references of the form
  `os.environ/VAR_NAME`; these are resolved only when the provider is created.
- Provider instances are cached per alias until reconfigured or reset.

### Module-level functions

```python
configure(name: str, provider: str | None = None, **kwargs) -> None
reset() -> None
acompletion(model: str, messages, *, tools=None, **params)
aembedding(model: str, input: list[str], **params)
aresponse(model: str, input, *, instructions=None, previous_id=None, tools=None, **params)
```

Behavioral notes:

- These are convenience wrappers around a shared default `LLMClient`.
- The default client follows the same alias, provider, and lazy-loading rules as
  an explicit `LLMClient` instance.

### Model strings and provider prefixes

`model` must use the form `provider/model-name` when a non-default provider is
wanted.

Supported prefixes:

- `openai/`
- `google/`
- `gemini/` alias for Google Gemini
- `anthropic/`
- `azure/`
- `azure_ai/`

Bare model names have no prefix and default to OpenAI routing.

Examples:

```python
await acompletion("gpt-4o", messages)                 # OpenAI default
await acompletion("openai/gpt-4o", messages)
await acompletion("gemini/gemini-2.0-flash", messages)
await aresponse("azure_ai/my-deployment", "Hello")
```

## Typed input shapes

### Chat messages

Public chat inputs accept both `TypedDict` message params and Pydantic message
models:

- `SystemMessageParam`, `DeveloperMessageParam`, `UserMessageParam`
- `AssistantMessageParam`, `ToolMessageParam`, `FunctionMessageParam`
- `SystemMessage`, `DeveloperMessage`, `UserMessage`
- `AssistantMessage`, `ToolMessage`, `FunctionMessage`

Convenience helpers in `giskard.llm.chat` create typed chat models:

```python
from giskard.llm.chat import user, assistant, system, developer, message
```

Role notes:

- Canonical roles are `system`, `developer`, `user`, `assistant`, and `tool`.
- `FunctionMessage` is still part of the type surface for compatibility, but
  providers differ in how they serialize or accept it.
- `ToolMessage` requires a `tool_call_id`.
- `assistant` messages may carry `refusal` text and/or `tool_calls`.

### Tool definitions

Public tool inputs use the nested Chat Completions shape:

```python
ToolDefParam = {
    "type": "function",
    "function": {
        "name": "...",
        "description": "...",
        "parameters": {...},
    },
}
```

Pydantic tool models are also available:

- `FunctionDef`
- `ToolDef`
- `FunctionDefParam`
- `ToolDefParam`

### Responses / function outputs

`aresponse(...)` accepts structured response input items and function results:

- `ResponseInputTextParam`
- `ResponseFunctionToolCallParam`
- `ResponseEasyInputMessageParam`
- `ResponseOutputMessageParam`
- `ResponseFunctionCallOutputParam` / `FunctionCallOutputParam`

Important: `FunctionCallOutputParam` includes `call_id`, `output`, and an
optional `name`, but Google Interactions uses `name` and therefore requires it
when the item is serialized there.

## Pydantic response types

The package returns Pydantic models with `model_dump(exclude_none=True)` behavior.
Key response types:

- `CompletionResponse`
- `Choice`
- `AssistantMessage`
- `ToolCall`
- `ToolCallFunction`
- `EmbeddingResponse`
- `EmbeddingData`
- `EmbeddingUsage`
- `ResponseResult`
- `ResponseOutputMessage`
- `ResponseFunctionToolCall`
- `ResponseOutputText`
- `ResponseOutputRefusal`
- `Usage`

Useful properties:

- `CompletionResponse.choices[0].message.content`
- `AssistantMessage.text` and `AssistantMessage.transcript`
- `ToolCallFunction.arguments`
- `EmbeddingResponse.data`
- `ResponseResult.outputs`
- `ResponseResult.output_text`
- `ResponseResult.function_calls`

`ToolCallFunction.arguments` is parsed into a `dict[str, object]` even when the
input is a JSON string.

## Errors and retry helper

```python
LLMError(status_code: int, message: str, provider: str)
AuthenticationError(...)
BadRequestError(...)
RateLimitError(...)
ServerError(...)
LLMTimeoutError(...)
UnsupportedOperationError(provider: str, operation: str)
ProviderNotAvailableError(provider: str, package: str, extra: str | None = None)
should_retry(error: Exception) -> bool
```

Retry guidance:

- `should_retry(...)` returns `True` for timeout, rate-limit, and server errors.
- Authentication, bad-request, unsupported-operation, and provider-availability
  errors are not retryable.
- Every provider error carries `status_code` so upstream retry middleware can use
  one consistent check.

## Provider capability summary

- OpenAI: completions, embeddings, and Responses API.
- Google Gemini: completions, embeddings, and Gemini Interactions.
- Anthropic: completions only.
- Azure OpenAI: completions, embeddings, and Responses API through the OpenAI SDK.
- Azure AI Foundry: OpenAI SDK routing for Foundry-style endpoints; completion
  support is primary and other behavior depends on the deployed model.
