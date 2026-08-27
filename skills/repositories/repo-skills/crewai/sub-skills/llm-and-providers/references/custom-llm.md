# Custom LLM

Use a custom LLM when CrewAI's native providers, OpenAI-compatible providers, and intentional LiteLLM fallback do not fit a target runtime, authentication scheme, local model wrapper, or test-double requirement.

## Minimal Contract

Custom LLMs should subclass `crewai.llms.base_llm.BaseLLM` or import `BaseLLM` from `crewai` when available. The constructor must call `super().__init__(model=..., temperature=...)` with at least a model name.

```python
from typing import Any
from crewai import BaseLLM

class MyLLM(BaseLLM):
    def __init__(self, model: str = "my-model", temperature: float | None = None):
        super().__init__(model=model, temperature=temperature)

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: type[Any] | None = None,
    ) -> str | Any:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        return "deterministic response"

    async def acall(self, *args: Any, **kwargs: Any) -> str | Any:
        raise NotImplementedError("Async calls are not implemented for this LLM")

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 4096
```

CrewAI calls `call()` with `messages`, optional tool schemas, optional callbacks, optional `available_functions`, and caller context (`from_task`, `from_agent`). Tests in CrewAI also exercise `response_model`, so include it in the signature even if the implementation ignores it.

## Message Handling

Accept both input forms:

- `"plain prompt"` should become `[ {"role": "user", "content": "plain prompt"} ]` before provider calls.
- A list of message dictionaries should preserve role/content values unless the target API requires a different shape.

For OpenAI/Anthropic-like APIs, text content can often be sent as strings or as structured blocks such as `[{"type": "text", "text": "..."}]`. If you normalize content, do it consistently for system, user, assistant, and tool messages.

## Function Calling Support

Return `True` from `supports_function_calling()` only when the custom provider can complete the full tool-use loop:

1. Accept tool schemas in the provider's expected format.
2. Detect tool/function calls from the provider response.
3. Look up callable implementations in `available_functions` by name.
4. Execute the callable or return a structured tool-call result in the format CrewAI expects.
5. Continue or finalize the message flow without losing tool-call IDs and arguments.

If a provider only returns text, return `False`. This is safer than advertising function calling and causing agents to stall or hallucinate tool results.

## Stop Words

CrewAI may use stop sequences such as `Observation:` in agent loops. Implement one of these patterns:

- If the backend supports stop sequences, pass `self.stop_sequences` through and return `True` from `supports_stop_words()`.
- If the backend does not support stop sequences, return `False` and optionally truncate generated text locally at the first configured stop sequence.

`BaseLLM` stores stop values under `stop` and exposes the active list as `stop_sequences`; the alias handles both `stop` and `stop_sequences` initialization.

## Context Windows

Override `get_context_window_size()` for local or custom models. The default base implementation is conservative. A correct value helps CrewAI reason about context pressure, but it is not a substitute for server-side limits.

```python
def get_context_window_size(self) -> int:
    return 32768
```

If the provider returns a context-length error, raise a clear exception that includes the model name and configured context window. Do not silently truncate user content unless the calling workflow asked for that behavior.

## Structured Output

CrewAI can pass `response_model` to `call()` and can also configure `LLM(response_format=...)` for built-in providers. A custom LLM has three safe choices:

- Ignore `response_model` and return text when structured parsing is handled elsewhere.
- Ask the provider for JSON/schema output if it supports it, then validate into the model.
- Return a Pydantic model instance only when the caller expects structured output.

Avoid claiming JSON support if the provider cannot reliably enforce valid JSON. Route task-level `output_json`, `output_pydantic`, and `response_model` placement to the core runtime sub-skill.

## Error Handling

Raise provider-specific failures as clear Python exceptions:

- `ValueError` for invalid constructor arguments, missing auth, malformed responses, or unsupported tool/response-model combinations.
- `TimeoutError` for request timeouts.
- `RuntimeError` or provider-native exceptions for transport failures after adding context such as model name and endpoint category.

Do not swallow authentication errors. Do not print secrets. Mask tokens in logs if you include headers or URLs.

## Safe Test Double Pattern

For unit tests or offline examples, implement a deterministic custom LLM that never calls network services:

```python
class StaticLLM(BaseLLM):
    def __init__(self, response: str = "ok"):
        super().__init__(model="static-test-model")
        self.response = response
        self.calls = []

    def call(self, messages, tools=None, callbacks=None, available_functions=None, from_task=None, from_agent=None, response_model=None):
        self.calls.append({"messages": messages, "tools": tools})
        return self.response

    async def acall(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def supports_function_calling(self) -> bool:
        return False
```

Use this pattern for local validation of `Agent`, `Task`, and `Crew` composition without credentials. Route the crew composition itself to [../../core-runtime/SKILL.md](../../core-runtime/SKILL.md).

## Custom Auth Pattern

For private providers, keep credentials outside public code:

```python
import os

class HeaderAuthLLM(BaseLLM):
    def __init__(self, endpoint: str, model: str = "private-model"):
        super().__init__(model=model)
        self.endpoint = endpoint
        self.token_env = "PRIVATE_LLM_TOKEN"

    def _token(self) -> str:
        token = os.getenv(self.token_env)
        if not token:
            raise ValueError(f"Set {self.token_env} before calling this LLM")
        return token
```

Never put the actual token into `to_config_dict()`, logs, trace metadata, or generated docs.

## Checklist

Before using a custom LLM in a CrewAI workflow:

- Constructor calls `super().__init__(model=...)`.
- `call()` accepts CrewAI's current keyword arguments.
- `acall()` is implemented or intentionally raises `NotImplementedError` with a clear message.
- `supports_function_calling()` matches real backend capability.
- `supports_stop_words()` and local stop handling are deliberate.
- `get_context_window_size()` returns a realistic number.
- Authentication errors and malformed responses have actionable messages.
- Offline tests use a deterministic test double rather than a live hosted model.

## Reference Notes

This reference adapts the public custom-LLM pattern and CrewAI tests into bundled guidance. No source test or doc file is required at runtime.
