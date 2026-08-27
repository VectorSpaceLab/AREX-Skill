# API Reference for Model Clients, Generator, and Embedder

This file records current verified AdalFlow API facts needed for model-client/generator workflows. Prefer these signatures over guesses when drafting code.

## Core signatures

```text
Generator.__init__(
    *,
    model_client: ModelClient,
    model_kwargs: Dict = {},
    model_type: Optional[ModelType] = ModelType.LLM,
    template: Optional[str] = None,
    prompt_kwargs: Optional[Dict] = {},
    output_processors: Optional[DataComponent] = None,
    name: Optional[str] = None,
    cache_path: Optional[str] = None,
    use_cache: bool = True,
)

Generator.call(
    prompt_kwargs: Optional[Dict] = {},
    model_kwargs: Optional[Dict] = {},
    use_cache: Optional[bool] = None,
    id: Optional[str] = None,
) -> GeneratorOutput

Generator.acall(
    prompt_kwargs: Optional[Dict] = {},
    model_kwargs: Optional[Dict] = {},
    use_cache: Optional[bool] = None,
    id: Optional[str] = None,
) -> GeneratorOutput

Embedder.__init__(
    *,
    model_client: ModelClient,
    model_kwargs: Dict[str, Any] = {},
    output_processors: Optional[DataComponent] = None,
)

Embedder.call(input: str | list[str], model_kwargs: Optional[Dict] = {}) -> EmbedderOutput
Embedder.acall(input: str | list[str], model_kwargs: Optional[Dict] = {}) -> EmbedderOutput

BatchEmbedder.__init__(embedder: Embedder, batch_size: int = 100)
BatchEmbedder.call(input: str | list[str], model_kwargs: Optional[Dict] = {}) -> list[EmbedderOutput]

Prompt.__init__(template: Optional[str] = None, prompt_kwargs: Optional[Dict[str, Any | Parameter]] = {})
Prompt.call(**kwargs) -> str
```

## `ModelClient` abstract protocol

```text
ModelClient.init_sync_client(self)
ModelClient.init_async_client(self)
ModelClient.call(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED)
ModelClient.acall(self, api_kwargs: Dict = {}, model_type: ModelType = ModelType.UNDEFINED)
ModelClient.convert_inputs_to_api_kwargs(
    self,
    input: Optional[Any] = None,
    model_kwargs: Dict = {},
    model_type: ModelType = ModelType.UNDEFINED,
) -> Dict
ModelClient.parse_chat_completion(self, completion: Any) -> GeneratorOutput
ModelClient.track_completion_usage(self, *args, **kwargs) -> CompletionUsage
ModelClient.parse_embedding_response(self, response: Any) -> EmbedderOutput
ModelClient.list_models(self)
```

Minimum concrete fake clients should implement every method that the test path touches. For a `Generator` test, the key methods are `convert_inputs_to_api_kwargs`, `call`/`acall`, and `parse_chat_completion`. For an `Embedder` test, also implement `parse_embedding_response` and ensure `call`/`acall` branches on `ModelType.EMBEDDER`.

## `ModelType`

```text
ModelType.EMBEDDER
ModelType.LLM
ModelType.LLM_REASONING
ModelType.RERANKER
ModelType.IMAGE_GENERATION
ModelType.UNDEFINED
```

`get_model_args(model_type)` reports common required `model_kwargs` keys:

- `EMBEDDER`: `model`
- `LLM`: `model`
- `RERANKER`: `model`, `top_k`, `documents`, `query`
- other values: no common required keys

Provider clients may require additional provider-specific fields.

## `GeneratorOutput` fields

`GeneratorOutput` is a dataclass-like `DataClass` used for all generator results.

| Field | Meaning |
|---|---|
| `id` | Caller-provided record id. |
| `input` | Rendered prompt string. |
| `data` | Final output after provider parsing and optional output processors. |
| `thinking` | Reasoning/thinking text when a compatible client extracts it. |
| `tool_use` | Tool-call representation when a client populates it. |
| `images` | Generated image URLs/base64 strings when supported. |
| `error` | Error message from model call or output processing. `None` means success. |
| `usage` | Token/usage object when available. |
| `raw_response` | Parsed raw response text, sync iterable, or async iterable. |
| `api_response` | Original provider response object when stored by the caller/client. |
| `metadata` | Optional client-specific metadata. |

Useful method:

```text
GeneratorOutput.stream_events() -> async iterator
```

`stream_events()` yields events from an async `raw_response`; if no stream was yielded and `data` exists, it yields `data`.

Image helper:

```text
GeneratorOutput.save_images(directory=".", prefix="generated", format="png", decode_base64=True, return_paths=True)
```

Use the image helper only when `images` is populated and the runtime path is intentionally chosen by the caller.

## `EmbedderOutput` and `Embedding`

`Embedding`:

```text
Embedding(embedding: list[float], index: Optional[int])
```

`EmbedderOutput` fields:

| Field | Meaning |
|---|---|
| `data` | List of `Embedding` objects. |
| `model` | Provider model name when available. |
| `usage` | Embedding token usage when available. |
| `error` | Error message if embedding or output processing failed. |
| `raw_response` | Raw provider response, usually only needed for errors/debugging. |
| `input` | Input text list passed to the embedder. |

Properties:

- `length`: number of embedding objects.
- `embedding_dim`: vector dimension, or `-1` when no embedding is available.

## Prompt composition facts

`Prompt` extracts undeclared Jinja2 variables from the template and composes final kwargs from:

1. variables discovered in the template, initialized to `None`,
2. constructor `prompt_kwargs`,
3. call-time kwargs.

`Prompt.call(**kwargs)` renders the final template. `Generator.get_prompt(**kwargs)` wraps this for the generator's configured template and preset prompt kwargs.

`Prompt` can render nested `Prompt` or Jinja `Template` values in prompt kwargs, but avoid circular prompt/template references.

## Generator execution sequence

Synchronous `Generator.call` does:

1. Render prompt with `get_prompt` and store it in `GeneratorOutput.input`.
2. Compose constructor and call-time `model_kwargs`.
3. Convert prompt/model kwargs to provider `api_kwargs` via `model_client.convert_inputs_to_api_kwargs`.
4. Optionally check cache by JSON-serialized `api_kwargs`.
5. Call `model_client.call(api_kwargs, model_type)`.
6. Save non-streaming completion to cache when caching is enabled.
7. Parse completion with `model_client.parse_chat_completion`.
8. Apply `output_processors` to `raw_response` when configured.
9. Populate callbacks/tracing attributes and return `GeneratorOutput`.

Async `Generator.acall` follows the same structure with `model_client.acall`. If parsed `raw_response` is an async iterable, the output's `raw_response` becomes an async processing iterator.

Training `Generator.forward` wraps inputs/outputs in optimization `Parameter` objects and delegates to `call` or a teacher generator. It is not the right entry point for simple inference.

## Configuration constructors

Both `Generator.from_config` and `Embedder.from_config` require a `model_client` component entry. Example shape:

```python
config = {
    "model_client": {
        "component_name": "OpenAIClient",
        "component_config": {},
    },
    "model_kwargs": {"model": "gpt-4o-mini", "temperature": 0},
}

generator = Generator.from_config(config)
```

Provider configuration still requires optional SDKs and credentials at runtime.

## Current-version import facts

- Importing `Generator` can require the `openai` Python package because generator streaming support imports OpenAI Response event types at module import time.
- Optional MLflow-related messages are tracing concerns and can be ignored for generator/provider workflows unless the task explicitly uses tracing.
- Provider clients are lazily imported from `adalflow.components.model_client`; missing extras usually surface only when that client is instantiated or used.
