# LangExtract API Map

Read this when you need a compact map of public APIs, data objects, provider configuration surfaces, and bundled helper locations. Detailed workflows live in the nearest sub-skill references.

## Public package entry points

```python
import langextract as lx
```

Top-level convenience functions:

- `lx.extract(*args, **kwargs)` forwards to `langextract.extraction.extract(...)`.
- `lx.visualize(*args, **kwargs)` forwards to `langextract.visualization.visualize(...)`.

Lazy submodules exposed from `langextract` include `data`, `schema`, `factory`, `providers`, `io`, `visualization`, `resolver`, `prompt_validation`, `prompting`, `tokenizer`, `exceptions`, and `core`.

## Extraction API

The effective implementation signature is documented in [sub-skills/extraction/references/workflows.md](../sub-skills/extraction/references/workflows.md). The most common arguments are:

- `text_or_documents`: literal text string or iterable of `lx.data.Document` objects.
- `prompt_description`: extraction instructions.
- `examples`: list of `lx.data.ExampleData`; required unless `output_schema` or a preconfigured output-schema model is active.
- `model_id`, `api_key`, `config`, `model`, `model_url`, `language_model_params`: provider/back-end controls; see [providers](../sub-skills/providers/SKILL.md).
- `max_char_buffer`, `batch_length`, `max_workers`, `extraction_passes`, `context_window_chars`: chunking, parallelism, and recall/cost controls.
- `resolver_params`: parsing/alignment controls such as `suppress_parse_errors`, `extraction_index_suffix`, fuzzy alignment threshold/algorithm/density, and `accept_match_lesser`.
- `output_schema`: LangExtract JSON envelope schema for supported Gemini/OpenAI structured output.
- `fetch_urls`: keyword-only trusted-URL fetch opt-in; default is literal text.
- `prompt_validation_level`, `prompt_validation_strict`: example-alignment checks.
- `tokenizer`: pass `langextract.core.tokenizer.UnicodeTokenizer()` for CJK/non-spaced/grapheme-sensitive text.

## Data objects

```python
lx.data.ExampleData(text: str, extractions: list[lx.data.Extraction])
lx.data.Extraction(
    extraction_class: str,
    extraction_text: str,
    *,
    char_interval=None,
    alignment_status=None,
    extraction_index=None,
    group_index=None,
    description=None,
    attributes=None,
)
lx.data.Document(text: str, *, document_id=None, additional_context=None)
lx.data.AnnotatedDocument(*, document_id=None, extractions=None, text=None)
lx.data.CharInterval(start_pos=None, end_pos=None)
```

`Extraction.char_interval` is the grounding signal used by downstream review and visualization. `attributes` can encode relationships or metadata but are not independently source-aligned spans.

## Schema helpers

Use [sub-skills/extraction/references/workflows.md](../sub-skills/extraction/references/workflows.md) for examples.

```python
lx.schema.extraction_item_schema(
    extraction_class,
    *,
    attributes=None,
    additional_properties=False,
)

lx.schema.extractions_schema(
    item_schema,
    *additional_item_schemas,
    additional_properties=False,
)
```

The helpers build the top-level `{"extractions": [...]}` envelope expected by LangExtract. Attribute objects use `<extraction_class>_attributes` keys. Do not use generic raw keys such as `extraction_text` inside the raw output item schema.

## Prompt validation and resolver controls

```python
from langextract.prompt_validation import PromptValidationLevel

PromptValidationLevel.OFF
PromptValidationLevel.WARNING
PromptValidationLevel.ERROR
```

Prompt validation aligns each few-shot example's `extraction_text` against its own example `text`. Strict mode treats fuzzy and lesser matches as errors in `ERROR` mode.

Resolver/alignment parameters are passed through `resolver_params`, for example:

```python
resolver_params = {
    "suppress_parse_errors": True,
    "enable_fuzzy_alignment": True,
    "fuzzy_alignment_threshold": 0.75,
    "fuzzy_alignment_algorithm": "lcs",
    "fuzzy_alignment_min_density": 1 / 3,
    "accept_match_lesser": True,
}
```

See [sub-skills/extraction/references/troubleshooting.md](../sub-skills/extraction/references/troubleshooting.md) for symptom-based tuning.

## Provider and factory APIs

```python
from langextract import factory

factory.ModelConfig(model_id=None, provider=None, provider_kwargs={})
factory.create_model(config, examples=None, use_schema_constraints=False, fence_output=None, return_fence_output=False, output_schema=None)
factory.create_model_from_id(model_id=None, provider=None, *, output_schema=None, **provider_kwargs)
```

Built-in providers:

- Gemini: `model_id` begins with `gemini`; supports API-key and Vertex AI modes.
- OpenAI: GPT-style IDs such as `gpt-4...` and `gpt-5...`; install `langextract[openai]`.
- Ollama: local model IDs such as `gemma`, `llama`, `qwen`, `deepseek`, `gpt-oss`, and selected Hugging Face style patterns.

No-network diagnostics:

```bash
python sub-skills/providers/scripts/check_provider_routes.py
```

See [sub-skills/providers/references/providers.md](../sub-skills/providers/references/providers.md) for batch config and provider-specific kwargs.

## I/O and visualization APIs

```python
lx.io.save_annotated_documents(annotated_documents, output_dir=None, output_name="data.jsonl", show_progress=True)
lx.io.load_annotated_documents_jsonl(jsonl_path, show_progress=True)
langextract.visualization.visualize(data_source, *, animation_speed=1.0, show_legend=True, gif_optimized=True)
```

`lx.visualize(...)` can take an `AnnotatedDocument` or JSONL path. A JSONL path visualizes the first document in the file; load/select a document yourself for multi-document outputs. See [sub-skills/visualization/references/workflows.md](../sub-skills/visualization/references/workflows.md).

## Custom provider plugin APIs

Plugin providers inherit `langextract.core.base_model.BaseLanguageModel` and implement:

```python
def infer(self, batch_prompts, **kwargs):
    for prompt in batch_prompts:
        yield [langextract.core.types.ScoredOutput(score=1.0, output=text)]
```

Register patterns with `langextract.providers.router.register(...)`. Implement a `BaseSchema` subclass only when the backend can steer structured output. Use the bundled scaffold generator:

```bash
python sub-skills/provider-plugins/scripts/create_provider_plugin.py MyProvider --with-schema --patterns '^my-model'
```

See [sub-skills/provider-plugins/references/plugin-authoring.md](../sub-skills/provider-plugins/references/plugin-authoring.md).
