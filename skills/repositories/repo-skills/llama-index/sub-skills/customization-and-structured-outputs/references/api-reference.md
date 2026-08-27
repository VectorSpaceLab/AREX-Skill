# API Reference

## Verified Package Facts

- Core package imports as `llama_index.core`.
- `llama-index-core==0.14.22` and `llama-index-workflows==2.22.0` were verified in the inspection environment.
- `pip check` passed during inspection.
- Deprecated `ServiceContext` should not be used for new code; use `Settings` and explicit constructor overrides.

## Settings

Import:

```python
from llama_index.core import Settings
```

Important mutable defaults:

- `Settings.llm`: lazily resolves the default LLM unless explicitly set.
- `Settings.embed_model`: lazily resolves the default embedding model unless explicitly set.
- `Settings.callback_manager`: defaults to `CallbackManager()` and propagates to resolved LLM/embed/parser objects.
- `Settings.node_parser` / `Settings.text_splitter`: defaults to `SentenceSplitter()`.
- `Settings.transformations`: defaults to `[Settings.node_parser]`.
- `Settings.tokenizer`: wraps global tokenizer setup.
- `Settings.prompt_helper` and `Settings.chat_prompt_helper`: derive prompt context/output metadata.
- `Settings.chunk_size` and `Settings.chunk_overlap`: delegate to the current node parser when it supports those attributes.
- `Settings.pydantic_program_mode`: delegates to the current LLM.

Use hidden fields (`Settings._llm`, `_embed_model`, `_callback_manager`, `_node_parser`, `_transformations`, `_prompt_helper`, `_chat_prompt_helper`) only for snapshot/restore in tests; public runtime code should use the property setters.

## Mock Models for Tests

Imports:

```python
from llama_index.core.llms import MockLLM
from llama_index.core.embeddings import MockEmbedding
```

Use cases:

- `MockLLM(max_tokens=...)` for no-provider LLM smoke checks.
- `MockEmbedding(embed_dim=...)` for deterministic embedding-dependent tests.
- A custom fake LLM may be more appropriate when structured-output tests require exact JSON content.

The LLM and embedding resolvers also support explicit disabling paths internally, but for skill examples prefer direct mock objects because they are clear and deterministic.

## Prompt Templates

Imports:

```python
from llama_index.core.prompts import PromptTemplate, ChatPromptTemplate
from llama_index.core.base.llms.types import ChatMessage, MessageRole
```

`PromptTemplate` constructor highlights:

```python
PromptTemplate(
    template: str,
    prompt_type: str = PromptType.CUSTOM,
    output_parser: BaseOutputParser | None = None,
    metadata: dict | None = None,
    template_var_mappings: dict | None = None,
    function_mappings: dict | None = None,
    **kwargs,
)
```

Useful methods:

- `format(**kwargs) -> str`
- `format_messages(**kwargs) -> list[ChatMessage]`
- `partial_format(**kwargs) -> PromptTemplate`
- `get_template() -> str`

`ChatPromptTemplate` accepts a sequence of `ChatMessage` templates and exposes the same formatting interface.

## Output Parsers

Import:

```python
from llama_index.core.output_parsers import PydanticOutputParser
```

Constructor:

```python
PydanticOutputParser(
    output_cls,
    excluded_schema_keys_from_format: list | None = None,
    pydantic_format_tmpl: str = PYDANTIC_FORMAT_TMPL,
)
```

Important behavior:

- `format_string` and `get_format_string()` produce JSON-schema instructions.
- `format(query)` appends those instructions to a query string.
- `parse(text)` extracts a JSON object from text and validates it via `output_cls.model_validate_json(...)`.
- Parser failures generally surface as JSON extraction or Pydantic validation errors.

## Pydantic Programs

Import:

```python
from llama_index.core.program import LLMTextCompletionProgram
```

Factory behavior:

```python
LLMTextCompletionProgram.from_defaults(
    output_parser=None,
    output_cls=None,
    prompt_template_str=None,
    prompt=None,
    llm=None,
    verbose=False,
    **kwargs,
)
```

Rules verified from source:

- You must provide exactly one of `prompt_template_str` or `prompt`.
- If `output_cls` is omitted, `output_parser` must be a `PydanticOutputParser` so the program can infer the model class.
- If `output_cls` is provided and `output_parser` is omitted, the factory creates `PydanticOutputParser(output_cls=output_cls)`.
- If `llm` is omitted, the program uses `Settings.llm`.
- `__call__`, `acall`, `stream_call`, and `astream_call` validate parser output is an instance of the expected output class.

## Structured LLM

`llm.as_structured_llm(OutputModel)` returns a wrapper that validates completions/chat responses against `OutputModel`. Internally, structured calls use structured prediction with `output_cls` and raise if the returned object is not an instance of the expected model.

Use this when the selected LLM integration supports structured prediction well. If the provider does not support strict schemas, fall back to `PydanticOutputParser` plus prompt instructions and retry/repair logic.

## Response Synthesizers

Import:

```python
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.response_synthesizers import ResponseMode
```

Verified factory parameters include:

```python
get_response_synthesizer(
    llm=None,
    prompt_helper=None,
    chat_prompt_helper=None,
    text_qa_template=None,
    refine_template=None,
    summary_template=None,
    simple_template=None,
    chat_content_qa_template=None,
    chat_content_refine_template=None,
    chat_summary_template=None,
    response_mode=ResponseMode.COMPACT,
    callback_manager=None,
    use_async=False,
    streaming=False,
    structured_answer_filtering=False,
    output_cls=None,
    program_factory=None,
    verbose=False,
    multimodal=False,
)
```

`output_cls` is forwarded to refine/compact/tree-summarize/accumulate modes that support structured output. `structured_answer_filtering` is available on refine and compact refine paths.

## Callbacks

Imports:

```python
from llama_index.core.callbacks import CallbackManager
from llama_index.core.callbacks import TokenCountingHandler, LlamaDebugHandler
from llama_index.core.callbacks import CBEventType, EventPayload
```

`CallbackManager(handlers=None)`:

- Stores a list of `BaseCallbackHandler` instances.
- Propagates configured global handlers if present.
- Supports `add_handler`, `remove_handler`, and `set_handlers`.
- Emits event lifecycle with `on_event_start`, `on_event_end`, and the `event(...)` context manager.
- Supports trace lifecycle with `as_trace(...)`, `start_trace(...)`, and `end_trace(...)`.

Set `Settings.callback_manager` before building components when you want global propagation to LLMs, embedding models, node parsers, query engines, and synthesizers that use settings defaults.

## Instrumentation

Core modules:

- `llama_index.core.instrumentation.dispatcher`
- `llama_index.core.instrumentation.events.*`
- `llama_index.core.instrumentation.event_handlers.*`
- `llama_index.core.instrumentation.span_handlers.*`

Use instrumentation for dispatcher/span/event integrations and callbacks for simpler local event counting or token counting.

## Evaluation

Imports:

```python
from llama_index.core.evaluation import EvaluationResult
```

`EvaluationResult` fields:

- `query: str | None`
- `contexts: Sequence[str] | None`
- `response: str | None`
- `passing: bool | None`
- `feedback: str | None`
- `score: float | None`
- `pairwise_source: str | None`
- `invalid_result: bool`
- `invalid_reason: str | None`

Evaluator base behavior:

- `evaluate(...)` synchronously runs `aevaluate(...)`.
- `evaluate_response(query=..., response=Response(...))` extracts `response.response` and each source node's content into evaluator inputs.
- Most built-in semantic evaluators are LLM-backed and require provider setup; custom/unit tests can assert `EvaluationResult` shape without external calls.
