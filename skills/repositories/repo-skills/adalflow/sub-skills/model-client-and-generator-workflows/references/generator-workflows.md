# Generator, Prompt, Cache, Streaming, and Embedder Workflows

This reference covers AdalFlow model orchestration surfaces owned by this sub-skill: `Generator`, `ModelClient`, output processors, cache behavior, provider-level streaming, fake-client tests, `Embedder`, and `BatchEmbedder`.

## Mental model

A `Generator` is an orchestration component around three pieces:

1. `Prompt`: renders a Jinja2 template from preset `prompt_kwargs` plus call-time `prompt_kwargs`.
2. `ModelClient`: converts rendered prompt plus `model_kwargs` into provider `api_kwargs`, calls the provider, and parses the provider response.
3. `output_processors`: optional `DataComponent` or chained component that parses the model text into the shape the pipeline needs.

A typical text generator has this shape:

```python
from adalflow.core.generator import Generator
from adalflow.components.model_client import OpenAIClient
from adalflow.core.string_parser import JsonParser

json_generator = Generator(
    model_client=OpenAIClient(),
    model_kwargs={"model": "gpt-4o-mini", "temperature": 0},
    template="Return JSON only for: {{ question }}",
    output_processors=JsonParser(),
    use_cache=False,
)

result = json_generator.call(prompt_kwargs={"question": "2 + 2?"})
if result.error:
    raise RuntimeError(result.error)
print(result.data)
```

Use a live provider only when its SDK, authentication, network, and budget are intentionally available. For local unit tests, use a fake `ModelClient` instead of a real client.

## Prompt rendering

`Generator.__init__` accepts a custom `template` and preset `prompt_kwargs`. When `template` is omitted, AdalFlow uses its default system prompt template. `Generator.get_prompt(**kwargs)` renders the prompt without calling a model.

Practical rules:

- Treat the template as Jinja2. Use variables such as `{{ input_str }}` or `{{ question }}`.
- Use `prompt_kwargs` in the constructor for stable instructions, examples, parser format strings, tool descriptions, or reusable context.
- Use call-time `prompt_kwargs` for record-specific inputs.
- Call-time keys override or complete preset keys.
- Inspect rendered prompts with `get_prompt` or `print_prompt` before changing provider settings.
- When passing parser format instructions, put the parser's format string in a prompt variable and pass the parser as `output_processors`.

Example with parser instructions:

```python
from adalflow.components.output_parsers import JsonOutputParser
from adalflow.core.types import Function

parser = JsonOutputParser(
    data_class=Function,
    return_data_class=True,
    include_fields=["thought", "name", "kwargs"],
)

planner = Generator(
    model_client=client,
    model_kwargs={"model": "provider-model"},
    template=(
        "{{ task_desc }}\n"
        "Use this output format:\n{{ output_format_str }}\n"
        "User task: {{ input_str }}"
    ),
    prompt_kwargs={
        "task_desc": "Choose the next tool call.",
        "output_format_str": parser.get_output_format_str(),
    },
    output_processors=parser,
)
```

## `model_kwargs` and `ModelType`

`model_kwargs` is not normalized across providers by `Generator`; it is passed to the selected `ModelClient`, which converts it into provider-specific `api_kwargs`.

Common keys:

- LLM clients usually require `{"model": "..."}`.
- Embedding clients usually require `{"model": "..."}` and may accept provider-specific fields such as dimensions or encoding format.
- Streaming usually uses `{"stream": True}` when supported by that client.
- Multimodal OpenAI Response API paths use `images` in `model_kwargs`; see `model-clients.md` and `troubleshooting.md`.

`Generator` combines constructor `model_kwargs` with call-time `model_kwargs`, with call-time values taking precedence.

Important current-version behavior: in `Generator._pre_call`, a `max_tokens` key is interpreted as a prompt-length guard, may truncate an overlong rendered prompt, and is removed before the provider call. If you need a provider output-token limit, verify the provider client's expected key and behavior before relying on `max_tokens` in `Generator.model_kwargs`.

Use `ModelType` deliberately:

- `ModelType.LLM`: standard language generation.
- `ModelType.LLM_REASONING`: reasoning-model-compatible LLM endpoints when the client supports them.
- `ModelType.EMBEDDER`: embeddings through `Embedder`, not `Generator`.
- `ModelType.IMAGE_GENERATION`: provider-specific image generation; confirm sync/async support for the selected client.
- `ModelType.RERANKER`: reranking clients, not owned by this generator workflow.

## `call`, `acall`, `forward`, and `__call__`

`Generator.call(prompt_kwargs={}, model_kwargs={}, use_cache=None, id=None)` is the normal synchronous inference method. It returns `GeneratorOutput`.

`Generator.acall(prompt_kwargs={}, model_kwargs={}, use_cache=None, id=None)` is the async inference method. It returns `GeneratorOutput`; if the model client yields an async stream, the output's `raw_response` is an async iterable.

`Generator.forward(...)` is for training/backpropagation workflows and returns a `Parameter`. Do not use it for ordinary inference unless the pipeline is intentionally in optimization/training mode.

`generator(...)` calls `forward` when `generator.training` is true and `call` otherwise. In most application and test code, prefer explicit `call`/`acall` so the control path is obvious.

## `GeneratorOutput` handling

Always inspect the structured fields instead of assuming raw text:

```python
out = generator.call(prompt_kwargs={"input_str": "Hello"})
if out.error:
    print("failed", out.error, out.raw_response)
elif out.data is not None:
    print("parsed/final", out.data)
else:
    print("raw", out.raw_response)
```

Key fields:

- `id`: caller-provided id, useful for datasets and tracing.
- `input`: rendered prompt string.
- `data`: final output, either raw text or output-processor result.
- `thinking`: reasoning text when a compatible client extracts it.
- `tool_use`: tool-call object when a client populates it.
- `images`: generated image payloads or URLs when supported.
- `error`: model call or output-processing error.
- `usage`: provider token/usage data when available.
- `raw_response`: parsed provider text or a streaming iterator.
- `api_response`: original provider object when available.
- `metadata`: additional client-specific metadata.

`Generator.call` catches provider-call exceptions and parser/output-processor exceptions and places the message in `GeneratorOutput.error`. Retrying blindly can hide parser bugs; inspect `raw_response` first.

## Output processors

`output_processors` must be a `DataComponent` instance. Built-in string parsers such as `JsonParser` are service-free. Output parsers for dataclasses are covered by the structured-I/O sub-skill, but they can be plugged into `Generator` here.

Rules:

- Processor input is the model client's parsed raw text (`output.raw_response`), not the original provider object.
- Processor output becomes `GeneratorOutput.data`.
- Processor exceptions are captured in `GeneratorOutput.error`.
- Chained processors should be deterministic and side-effect-free.
- For streaming responses, avoid structured output processors unless you first collect a complete final text. Stream chunks are not usually valid complete JSON/YAML.

## Cache behavior

`Generator` inherits a disk-backed cache engine. Constructor argument `use_cache` defaults to `True`; `call(..., use_cache=...)` overrides it per call.

Operational guidance:

- Disable caching for tests that assert call counts, changing prompts, dynamic provider parameters, or privacy-sensitive prompts.
- Streaming responses are not saved to cache because streaming objects are not safely serializable.
- Cache keys are based on JSON-serialized `api_kwargs`; keep `model_kwargs` JSON-serializable when cache is enabled.
- The cache path is per client class and model name with a sanitized filename. If `cache_path` is omitted, AdalFlow chooses its configured default root.
- Cache hits can make it look as if a provider call did not happen. Re-run with `use_cache=False` when debugging.
- Changing only local parser code does not invalidate cached provider completions; you may still get the same `raw_response` with new parsing behavior.

## Streaming basics

Streaming support belongs partly to the provider client. Most clients use `model_kwargs={"stream": True}` when streaming is available.

Synchronous pattern:

```python
response = generator.call(
    prompt_kwargs={"input_str": "Tell me a short story"},
    model_kwargs={"stream": True},
    use_cache=False,
)

if response.error:
    raise RuntimeError(response.error)

for event in response.raw_response:
    # Provider clients may yield raw chunks or normalized Response API events.
    handle(event)
```

Async pattern:

```python
response = await generator.acall(
    prompt_kwargs={"input_str": "Stream one sentence"},
    model_kwargs={"stream": True},
    use_cache=False,
)

async for event in response.stream_events():
    handle(event)
```

OpenAI Response API streaming utilities in `adalflow.components.model_client.utils` can extract text deltas from Response API events. Other providers may yield ChatCompletion chunks, Bedrock stream chunks, Ollama chunks, or converted events. Do not assume all streaming events share one schema.

## Fake-client tests

For deterministic tests, subclass `ModelClient` and implement the protocol methods. The fake should return `GeneratorOutput` from `parse_chat_completion`, not a bare string.

Minimal pattern:

```python
from adalflow.core.model_client import ModelClient
from adalflow.core.types import GeneratorOutput, ModelType

class FakeClient(ModelClient):
    def init_sync_client(self):
        return self

    def init_async_client(self):
        return self

    def convert_inputs_to_api_kwargs(self, input=None, model_kwargs={}, model_type=ModelType.UNDEFINED):
        return {"input": input, "model_type": model_type.name, **model_kwargs}

    def call(self, api_kwargs={}, model_type=ModelType.UNDEFINED):
        return {"text": '{"answer": "ok"}'}

    async def acall(self, api_kwargs={}, model_type=ModelType.UNDEFINED):
        return self.call(api_kwargs, model_type)

    def parse_chat_completion(self, completion):
        return GeneratorOutput(raw_response=completion["text"])
```

Run the bundled script for a fuller no-network check covering sync generation, async generation, JSON parsing, embeddings, and batching:

```bash
python scripts/generator_fake_client_smoke.py
```

Run it from this sub-skill directory or adjust the path to the bundled script.

## Embedder and BatchEmbedder

`Embedder` is the embedding analog of `Generator`:

```python
from adalflow.core.embedder import Embedder, BatchEmbedder
from adalflow.components.model_client import OpenAIClient

embedder = Embedder(
    model_client=OpenAIClient(),
    model_kwargs={"model": "text-embedding-3-small"},
)
output = embedder.call(["first document", "second document"])
```

Contract:

- Input is a single string or a list of strings.
- `Embedder` uses `ModelType.EMBEDDER` internally.
- The model client converts input to provider embedding kwargs and parses the provider embedding response to `EmbedderOutput`.
- `EmbedderOutput.data` is a list of `Embedding(embedding=[...], index=...)`.
- `EmbedderOutput.length` counts returned embeddings; `embedding_dim` reports vector dimension when data is present.
- `output_processors`, if provided, operate on embedding data, not text.
- `BatchEmbedder(embedder, batch_size=...)` slices large inputs into batches and returns a list of `EmbedderOutput` objects.

RAG-specific use of embeddings with `Document`, `ToEmbeddings`, retrievers, and vector stores belongs to `retrieval-rag-and-data-pipelines`. This sub-skill owns only provider-level embedding orchestration and testing.
