# Data formats and seed YAML schemas

This reference describes the data shapes an agent needs when using PyRIT converters, message normalization, and seed datasets. It avoids requiring the original repository checkout at runtime.

## Prompt data types

PyRIT's fine-grained `PromptDataType` values are string literals:

| Value | Typical use |
| --- | --- |
| `text` | Normal prompt/response text. Most offline text converters use this. |
| `image_path` | Local image file path. Some normalizers convert it to a data URL for chat APIs. |
| `audio_path` | Local audio file path. Chat normalization supports `.wav` and `.mp3` for input audio. |
| `video_path` | Local video file path. Requires target/converter support. |
| `binary_path` | Local binary file path, such as generated PDF/DOC output. |
| `url` | URL value. In `ChatMessageNormalizer`, this is treated as an image URL. |
| `reasoning` | Reasoning payloads for targets that expose them. |
| `error` | Error message payload. |
| `function_call`, `tool_call`, `function_call_output` | Tool/function-call message payloads. |

The media/path-like values are `image_path`, `audio_path`, `video_path`, and `binary_path`. Do not assume a target can consume a converter's output just because the converter produced it; target capability checks belong in `../targets-scorers/SKILL.md`.

## Converter output format

`convert_async()` and `convert_tokens_async()` return a `ConverterResult`:

```python
ConverterResult(output_text="...", output_type="text")
```

- `output_text` is the converted value. For media/file converters it can be a local path or URL-like string.
- `output_type` is a `PromptDataType` literal and becomes the next converter's input type in a stack.

If a converter raises `ValueError("Input type not supported")`, the supplied `input_type` did not match its `SUPPORTED_INPUT_TYPES`.

## Message and message-piece shape

A PyRIT `Message` groups one or more `MessagePiece` objects. Invariants enforced by the model:

- A `Message` must have at least one piece.
- All pieces in one `Message` must share `conversation_id`, `sequence`, and `role`.
- Every piece must have a non-`None` `converted_value`.
- The first piece's `api_role` represents the message role; `simulated_assistant` maps to `assistant` for API compatibility.

Minimal text message:

```python
from pyrit.models import Message

msg = Message.from_prompt(prompt="What is a safe test prompt?", role="user")
assert msg.get_piece().converted_value_data_type == "text"
```

Manual multipart message pattern:

```python
from pyrit.models import Message, MessagePiece

message = Message(
    message_pieces=[
        MessagePiece(role="user", sequence=0, original_value="Describe this image", original_value_data_type="text"),
        MessagePiece(role="user", sequence=0, original_value="sample.png", original_value_data_type="image_path"),
    ]
)
```

Use explicit `data_type`/`original_value_data_type` for file paths; otherwise string values are treated as text unless seed-path inference finds an existing known media file.

## `SeedPrompt` fields

Installed constructor signature summary:

```python
SeedPrompt(
    *,
    value: str,
    value_sha256: str | None = None,
    id: UUID | None = <factory>,
    name: str | None = None,
    dataset_name: str | None = None,
    harm_categories: list[str] | None = <factory>,
    description: str | None = None,
    authors: list[str] | None = <factory>,
    groups: list[str] | None = <factory>,
    source: str | None = None,
    date_added: aware datetime | None = <factory>,
    added_by: str | None = None,
    metadata: dict[str, Any] | None = <factory>,
    prompt_group_id: UUID | None = None,
    prompt_group_alias: str | None = None,
    is_general_technique: bool = False,
    is_jinja_template: bool = False,
    data_type: PromptDataType | None = None,
    seed_type: Literal["prompt"] = "prompt",
    response_json_schema: dict[str, Any] | None = None,
    role: Literal["system", "user", "assistant", "simulated_assistant", "tool", "developer"] | None = None,
    sequence: int = 0,
    parameters: list[str] | None = <factory>,
)
```

Field groups:

| Field(s) | Purpose |
| --- | --- |
| `value` | Required payload text or media/file path string. |
| `data_type` | Prompt modality. If omitted, `SeedPrompt` infers from an existing known media extension; otherwise uses `text`. |
| `role`, `sequence` | Conversation role and turn grouping. Same `sequence` values can be sent together in a multipart turn. |
| `prompt_group_alias` | YAML-friendly grouping key. `SeedDataset.from_dict()` converts aliases into shared generated group IDs. Do not pre-set `prompt_group_id` in YAML seed dicts. |
| `parameters` | Names that callers must supply when rendering a Jinja template. |
| `response_json_schema` / `response_json_schema_name` | Optional response-shape constraint. Set at most one. The `response_json_schema_name` input is consumed during construction and is not stored on the instance. |
| `harm_categories`, `authors`, `groups`, `source`, `metadata` | Provenance/filtering metadata. |

### Data-type inference

If `data_type` is omitted:

- Existing files with video extensions such as `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm` infer `video_path`.
- Existing files with audio extensions such as `.flac`, `.mp3`, `.m4a`, `.ogg`, `.wav` infer `audio_path`.
- Existing files with image extensions such as `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff` infer `image_path`.
- Existing files with unknown extensions raise `ValueError("Unable to infer data_type...")`.
- Long strings, invalid path strings, and ordinary text infer `text`.

For portable datasets, set `data_type` explicitly rather than relying on whether a file exists on the current machine.

## `SeedDataset` fields

`SeedDataset` is a collection wrapper with top-level defaults and a required non-empty `seeds` list:

```python
SeedDataset(
    data_type="text",
    name=None,
    dataset_name=None,
    harm_categories=None,
    description=None,
    authors=[],
    groups=[],
    source=None,
    date_added=<now>,
    added_by=None,
    seed_type=None,
    seeds=[...],
)
```

Rules:

- `seeds` cannot be empty or `None`.
- Dict entries default to `seed_type: "prompt"` unless the dataset or entry sets another seed type.
- Dataset-level scalar defaults (`name`, `description`, `source`, `dataset_name`) fill missing per-seed fields.
- Dataset-level list defaults (`harm_categories`, `authors`, `groups`) merge into per-seed lists with deterministic deduplication.
- Prompt seeds inherit dataset `data_type` and default `role: "user"` when omitted.
- Non-prompt seeds (`objective`, `simulated_conversation`) do not accept prompt-only fields (`data_type`, `role`, `sequence`, `parameters`); dataset normalization strips inherited prompt-only defaults before validating them.
- `.prompts`, `.objectives`, and `.seed_groups` properties provide typed subsets/groupings.
- `get_values(first=None, last=None, harm_categories=None)` returns prompt values; `get_random_values(number=..., harm_categories=None)` samples prompt values.

## Local YAML seed files

### Single `SeedPrompt` YAML

```yaml
value: "Summarize this benign sentence for {{ audience }}."
data_type: text
role: user
parameters:
  - audience
description: "Tiny local template for smoke testing."
```

Load and validate required parameters:

```python
from pyrit.models import SeedPrompt

prompt = SeedPrompt.from_yaml_with_required_parameters("template.yaml", ["audience"])
rendered = prompt.render_template_value(audience="students")
```

### `SeedDataset` YAML

Use `seeds:` as the top-level collection field in this version.

```yaml
dataset_name: tiny_local_dataset
name: Tiny local examples
description: Offline examples for converter/dataset smoke tests.
data_type: text
authors:
  - Example Author
groups:
  - smoke
source: local
seeds:
  - value: "Write a one-line summary of safe input."
    role: user
    sequence: 0
    prompt_group_alias: group_1
  - value: "Return exactly one sentence."
    role: system
    sequence: 0
    prompt_group_alias: group_1
```

Load:

```python
from pyrit.models import SeedDataset

dataset = SeedDataset.from_yaml_file("tiny_dataset.yaml")
assert dataset.dataset_name == "tiny_local_dataset"
assert len(dataset.seed_groups) == 1
```

YAML loader accommodations:

- The YAML top level must be a mapping and cannot be empty.
- Bare-string `harm_categories`, `authors`, `groups`, and `parameters` are wrapped into one-item lists by the YAML loader.
- Programmatic Pydantic construction is stricter: pass actual lists for list-typed fields.
- YAML files loaded through PyRIT seed loaders are marked trusted Jinja templates (`is_jinja_template=True`) at the loader boundary. Do not load unreviewed remote text as trusted YAML.

## Template rendering

`Seed.render_template_value(**kwargs)` uses Jinja `StrictUndefined` and raises `ValueError` when required variables are missing or invalid.

`Seed.render_template_value_silent(**kwargs)` preserves simple unresolved placeholders and avoids rendering control structures when loop variables are missing. YAML loading uses this silent render with PyRIT path defaults, so missing user-supplied placeholders can remain in the value until you explicitly render or validate them.

Best practice:

1. Declare every intended placeholder in `parameters`.
2. Use `SeedPrompt.from_yaml_with_required_parameters(path, required_parameters=[...])` for templates consumed by converters/scorers/attacks.
3. Before execution, call `render_template_value()` with concrete kwargs and handle `ValueError`.

## Response JSON schemas

A `SeedPrompt` can constrain a target/scorer response by setting either:

- `response_json_schema`: inline JSON Schema dictionary, or
- `response_json_schema_name`: name of a registered common schema.

Set at most one. If both are present, construction raises. If the name is unknown, construction raises.

Common schema names bundled in this version:

| Name | Required fields | Purpose |
| --- | --- | --- |
| `true_false_with_rationale` | `score_value` boolean, `rationale` string | Self-ask true/false response with rationale. |
| `scale_with_rationale` | `score_value` string, `description` string, `rationale` string | Scale/Likert response with rationale. |
| `adversarial_chat` | `next_message` string, `rationale` string, `last_response_summary` string | Structured adversarial-chat next-message response. |

When a target cannot enforce JSON schema natively, `JsonSchemaNormalizer` appends schema instructions to text message pieces and removes schema metadata from non-text pieces.

## Dataset metadata and filters

`SeedDatasetMetadata` fields are optional sets:

| Field | Examples/meaning |
| --- | --- |
| `tags` | Advisory tags such as `safety`, `multimodal`, `multilingual`, `privacy`, `jailbreak`, `bias`, `medical`, `legal`, `cybersecurity`, `refusal`, `synthetic`, `objectives`, `system_prompt`, `default`, `all`. |
| `size` | One of `tiny`, `small`, `medium`, `large`, `huge` by dataset convention. |
| `modalities` | High-level modalities such as `text`, `image`, `audio`, `video`. |
| `source_type` | `local` or `remote`. |
| `load_time` | `fast`, `normal`, `slow`, or `uninitialized`. |
| `harm_categories` | Dataset-specific or standardized harm labels. |

`SeedDatasetFilter` accepts either flat metadata kwargs or explicit `criteria=[SeedDatasetMetadata(...), ...]`. Criteria are ORed together; fields inside a criterion are ANDed. With `strict_match=False` (default), values inside one field match on any overlap. With `strict_match=True`, the filter values must be a subset of the dataset metadata values.

Special tags:

- `all` bypasses metadata filtering and returns every dataset name.
- `default` acts as a curated-set shortcut when `strict_match=False` and the dataset has the `default` tag.

Example:

```python
from pyrit.datasets.seed_datasets.seed_metadata import SeedDatasetFilter

fast_text_or_default = SeedDatasetFilter(tags={"default"}, modalities={"text"})
```

For CLI-based listing and scanner workflows, route to `../cli-backend-scanner/SKILL.md`.
