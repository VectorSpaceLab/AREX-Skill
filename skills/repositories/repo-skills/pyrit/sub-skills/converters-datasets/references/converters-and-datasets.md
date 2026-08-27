# Converter and dataset workflows

This reference is self-contained for PyRIT `1.1.0.dev0` and distills the converter, normalizer, message, and seed-dataset APIs that are safe to use from an installed `pyrit` package.

## Converter decision tree

| Need | Prefer | Notes |
| --- | --- | --- |
| Deterministic text obfuscation/encoding | Offline text-to-text converters such as `Base64Converter`, `SearchReplaceConverter`, `ROT13Converter`, `JsonStringConverter`, `SuffixAppendConverter`, `UrlConverter` | No credentials or network. Validate `SUPPORTED_INPUT_TYPES`/`SUPPORTED_OUTPUT_TYPES` first. |
| Convert only selected spans | `convert_tokens_async()` for `⟪...⟫` spans or `SelectiveTextConverter` with a selection strategy | Tokens only work with `input_type="text"`. Uneven start/end tokens raise `ValueError`. |
| Use LLM rewriting/translation/variation | LLM-backed converters such as `TranslationConverter`, `VariationConverter`, `ToneConverter`, `LLMGenericTextConverter` | Requires a chat-capable `converter_target`; configure targets in `../targets-scorers/SKILL.md`. |
| Create or transform media/files | Image/audio/video/file converters | Check modality, local file existence, and optional dependencies. Some converters call external services. |
| Pass converters into attack execution | `ConverterConfiguration` plus attack/executor-specific converter config | Build converter config here; execute through `../attacks-scenarios/SKILL.md`. |
| Load curated or custom prompts | `SeedPrompt`, `SeedDataset`, `SeedDatasetProvider` | Prefer local YAML for no-network work. Remote providers can download/cache data. |

## Core converter contract

Every concrete converter is a keyword-only class with these class attributes and methods:

- `SUPPORTED_INPUT_TYPES`: tuple of accepted `PromptDataType` values.
- `SUPPORTED_OUTPUT_TYPES`: tuple of produced `PromptDataType` values.
- `async convert_async(*, prompt: str, input_type: PromptDataType = "text") -> ConverterResult`.
- `async convert_tokens_async(*, prompt: str, input_type="text", start_token="⟪", end_token="⟫") -> ConverterResult`.
- `input_supported(input_type)` and `output_supported(output_type)` helpers.
- `supported_input_types` and `supported_output_types` instance properties.

`ConverterResult` has two public fields:

| Field | Meaning |
| --- | --- |
| `output_text: str` | Converted value. For media/file converters this can be a local path or URL-like value, not raw bytes. |
| `output_type: PromptDataType` | PyRIT data type of `output_text`, e.g. `text`, `image_path`, `audio_path`, `binary_path`. |

`get_converter_modalities()` returns sorted triples `(converter_class_name, input_modalities, output_modalities)` by reading each exported converter class. It is useful for planning, but direct class attributes are safer inside minimal smoke helpers because modality listing may import additional converter modules.

`NoOpConverter` is not exported from `pyrit.converter` in this checkout. To skip conversion, use `[]` for converter configurations rather than importing a no-op class.

## Installed offline converter facts

### `Base64Converter`

Signature:

```python
Base64Converter(*, encoding_func="b64encode")
```

Supported encoding names are `b64encode`, `urlsafe_b64encode`, `standard_b64encode`, `b2a_base64`, `b16encode`, `b32encode`, `a85encode`, and `b85encode`. It accepts only `text` and returns `text`.

Safe deterministic example:

```python
import asyncio
from pyrit.converter import Base64Converter

async def main():
    result = await Base64Converter().convert_async(prompt="hello", input_type="text")
    assert result.output_text == "aGVsbG8="
    assert result.output_type == "text"

asyncio.run(main())
```

`b2a_base64` is delegated to Python's `binascii.b2a_base64`, so expect that encoder's newline behavior.

### `SearchReplaceConverter`

Signature:

```python
SearchReplaceConverter(*, pattern: str, replace: str | list[str], regex_flags: int = 0)
```

It accepts only `text` and returns `text`. `pattern` is a Python regular expression. If `replace` is a list, one replacement is selected with `random.choice()` on every conversion; use a single string or one-item list for deterministic behavior.

Safe deterministic example:

```python
import asyncio
from pyrit.converter import SearchReplaceConverter

async def main():
    c = SearchReplaceConverter(pattern=r"\bsecret\b", replace="placeholder")
    result = await c.convert_async(prompt="replace secret only", input_type="text")
    assert result.output_text == "replace placeholder only"

asyncio.run(main())
```

## Converter stacks with `ConverterConfiguration`

`ConverterConfiguration` is the common unit used by `PromptNormalizer` and attack/executor configs:

```python
from pyrit.prompt_normalizer import ConverterConfiguration

cfg = ConverterConfiguration(
    converters=[converter_a, converter_b],
    indexes_to_apply=[0],                 # optional message-piece indexes
    prompt_data_types_to_apply=["text"],  # optional current converted data types
)
```

Behavior:

1. The normalizer iterates configurations in list order.
2. For each configuration, it visits message pieces by index.
3. If `indexes_to_apply` is set, only those piece indexes are converted.
4. If `prompt_data_types_to_apply` is set, only pieces whose *current* `converted_value_data_type` is in the list are converted.
5. Each converter in `converters` is applied sequentially to the piece's current value and data type.
6. The piece's `converted_value`, `converted_value_data_type`, and converter identifiers are updated.

`ConverterConfiguration.from_converters(converters=[...])` returns one configuration per converter with no index or data-type filters. It is a concise way to express a simple ordered stack.

### Offline stack validation pattern

Use this pattern before plugging a stack into an attack or target send:

```python
import asyncio
from pyrit.converter import Base64Converter, SearchReplaceConverter

async def validate_stack():
    value = "hello placeholder"
    dtype = "text"
    for converter in [SearchReplaceConverter(pattern="placeholder", replace="world"), Base64Converter()]:
        if not converter.input_supported(dtype):
            raise ValueError(f"{converter.__class__.__name__} does not accept {dtype}")
        result = await converter.convert_async(prompt=value, input_type=dtype)
        value, dtype = result.output_text, result.output_type
    return value, dtype

print(asyncio.run(validate_stack()))
```

Validate both the first converter's input type and the final output type expected by the target/scorer. Target capability questions belong in `../targets-scorers/SKILL.md`.

## Prompt normalization pipeline

`PromptNormalizer` applies converter configurations around target sends and stores messages in PyRIT memory. Initialize the PyRIT session and memory first via `../setup-memory-core/SKILL.md` when using this pipeline.

Important entry points:

| API | Purpose |
| --- | --- |
| `PromptNormalizer(start_token="⟪", end_token="⟫")` | Uses those tokens when applying converter `convert_tokens_async()`. |
| `send_prompt_async(message, target, conversation_id=None, request_converter_configurations=None, response_converter_configurations=None)` | Applies request converters, sends to target, stores request/response, applies response converters to the final response. |
| `send_prompt_batch_to_target_async(requests, target, batch_size=10)` | Batches `NormalizerRequest` values. |
| `convert_values_async(converter_configurations, message)` | Applies converters in-place to a `Message` without sending to a target. |
| `convert_audio_async(raw_pcm, converter_configurations, sample_rate_hz, num_channels, sample_width_bytes)` | Wraps PCM in a temporary WAV, applies audio-path converters, and validates that output PCM format still matches. |

`NormalizerRequest` contains a `Message`, request converter configurations, response converter configurations, and an optional `conversation_id`.

## Message normalizers

Message normalizers convert PyRIT `Message` objects into formats expected by specific targets. Use them when target code asks for a different chat/message representation.

| Normalizer | Output | Key details |
| --- | --- | --- |
| `ChatMessageNormalizer(use_developer_role=False, system_message_behavior="keep")` | list of `ChatMessage` objects, or JSON string through `normalize_string_async()` | Single text pieces become string content. Multipart/non-text pieces become content arrays. `image_path` becomes an image data URL, `audio_path` supports `.wav` and `.mp3`, and `url` is treated as an image URL. |
| `GenericSystemSquashNormalizer` | list of `Message` | Merges system messages into user messages for models that do not support system-role input. |
| `HistorySquashNormalizer` | list of `Message` | Squashes history for models with limited chat history support. |
| `ConversationContextNormalizer` | string | Formats non-system conversation turns as numbered context text. |
| `JsonSchemaNormalizer(schema_instructions_template=...)` | list of `Message` | For targets without native JSON schema support, appends schema instructions to text pieces and removes schema metadata from non-text pieces. Template must include `{schema_json}`. |
| `TokenizerTemplateNormalizer.from_model(...)` | string | Uses a HuggingFace tokenizer chat template. This can require the `transformers` stack, model downloads, and possibly a token; avoid it in no-network smoke tests. |

## Dataset provider workflow

### Programmatic seeds and datasets

Use `SeedPrompt` for a single prompt-like seed, and `SeedDataset` for a collection of `SeedPrompt`, `SeedObjective`, or `SeedSimulatedConversation` entries. See [data-formats.md](data-formats.md) for field-level schemas.

```python
from pyrit.models import SeedDataset, SeedPrompt

prompt = SeedPrompt(value="Review this benign test input.", data_type="text", role="user")
dataset = SeedDataset(dataset_name="tiny_local", seeds=[prompt])
assert dataset.get_values() == ["Review this benign test input."]
```

### Local YAML datasets

`SeedDataset.from_yaml_file(path)` loads a trusted local YAML mapping with a top-level `seeds:` list. Use it for self-contained custom datasets. The local dataset loader discovers `.prompt` and `.yaml` files bundled with PyRIT and exposes them through provider registration, but arbitrary user local files are normally loaded directly with `SeedDataset.from_yaml_file()` or `_LocalDatasetLoader(file_path=...)`.

### Registered providers

`SeedDatasetProvider` is the abstract provider interface. Concrete subclasses register automatically at import time and implement:

- `dataset_name` property.
- `async fetch_dataset_async(*, cache: bool = True) -> SeedDataset`.
- optional `_parse_metadata_async()` returning `SeedDatasetMetadata`.

Discovery and fetching APIs:

```python
from pyrit.datasets import SeedDatasetProvider
from pyrit.datasets.seed_datasets.seed_metadata import SeedDatasetFilter

names = await SeedDatasetProvider.get_all_dataset_names_async(
    filters=SeedDatasetFilter(tags={"default"})
)
# Fetch only an explicit small set; fetching every provider can be slow or network-heavy.
datasets = await SeedDatasetProvider.fetch_datasets_async(dataset_names=names[:1], cache=True)
```

Provider constraints:

- `get_all_dataset_names_async()` instantiates providers and parses metadata; it should not fetch full remote payloads, but import-time provider registration may load support modules.
- `fetch_datasets_async(dataset_names=None)` fetches every registered provider. Avoid this in smoke tests or constrained runs.
- `dataset_names` must match provider `dataset_name`; invalid names raise `ValueError` with the available names.
- `cache=True` lets remote loaders reuse cached files. `cache=False` may force remote re-downloads or temporary files.
- Remote loaders can fetch public URLs, local files, HuggingFace datasets, or selected ZIP members. They may need network, credentials/tokens, and time.
- Use `max_concurrency=1` for reproducibility or brittle networks; default is `5`.

## Local versus remote data guidance

| Situation | Recommended action |
| --- | --- |
| Need a no-secret/no-network example | Create `SeedPrompt`/`SeedDataset` programmatically or load a temporary local YAML. |
| Need curated built-in dataset names | Use provider name discovery or the CLI route in `../cli-backend-scanner/SKILL.md`. Do not fetch all providers without a budget. |
| Need a specific remote dataset | Fetch by exact `dataset_names=[...]`, document expected network/cache behavior, and keep `cache=True` unless freshness is required. |
| Need multimodal seeds | Set `data_type` explicitly (`image_path`, `audio_path`, `video_path`, etc.) and verify the downstream target accepts those modalities. |
| Need templates | Declare `parameters` on `SeedPrompt` YAML and validate required parameters before rendering. |
