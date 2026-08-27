# Pipeline API Reference

## Public Package Facts

- Distribution/import name: `transformers`.
- Inspected version: `5.13.0.dev0`.
- Primary inference API: `transformers.pipeline`.
- Related loading APIs: `AutoConfig.from_pretrained`, `AutoTokenizer.from_pretrained`, task-specific `AutoModel*` classes, processors, image processors, feature extractors, and video processors.
- Optional backend boundary: a minimal environment can import `transformers`, but PyTorch-dependent classes raise an optional dependency `ImportError` unless `torch` is installed.

## `pipeline()` Constructor

The inspected `pipeline` signature includes:

```python
pipeline(
    task=None,
    model=None,
    config=None,
    tokenizer=None,
    feature_extractor=None,
    image_processor=None,
    video_processor=None,
    processor=None,
    revision=None,
    use_fast=True,
    token=None,
    device=None,
    device_map=None,
    dtype="auto",
    trust_remote_code=None,
    model_kwargs=None,
    pipeline_class=None,
    **kwargs,
)
```

Important semantics:

- `task` selects a task-specific pipeline. If omitted, Transformers may infer the task from Hub model metadata when available.
- `model` accepts a Hub id, local path, or preloaded model object.
- `config`, `tokenizer`, `feature_extractor`, `image_processor`, `video_processor`, and `processor` can be explicit ids/paths/objects when automatic discovery is insufficient.
- `revision` pins a Hub branch, tag, or commit.
- `use_fast=True` prefers fast tokenizers/processors when available.
- `token` supplies Hub authentication for private or gated assets; do not embed secrets in code examples.
- `device` selects an execution device such as `-1`, `0`, `"cuda:0"`, or `"mps"`.
- `device_map` delegates placement to Accelerate-compatible loading, commonly `"auto"`.
- `dtype` replaces older `torch_dtype` usage; `dtype="auto"` is the default constructor value.
- `model_kwargs` passes options to model loading; avoid duplicating top-level `dtype` or `device_map` there.
- `pipeline_class` allows a custom pipeline class when implementing advanced extensions.
- `**kwargs` are forwarded to task-specific construction or calls, depending on the pipeline.

## Supported Task Families

Task names are lowercase hyphen identifiers. Common inspected tasks include:

| Family | Task ids | Typical input | Typical output signal |
| --- | --- | --- | --- |
| Text | `text-classification`, `sentiment-analysis`, `token-classification`, `ner`, `fill-mask`, `question-answering`, `zero-shot-classification`, `summarization`, `translation`, `text2text-generation`, `text-generation` | strings, pairs, dicts, or chat-like lists depending on task | labels/scores, generated text, spans, answers |
| Audio | `audio-classification`, `automatic-speech-recognition`, `text-to-audio`, `zero-shot-audio-classification` | audio file path, URL, array, or text prompt for text-to-audio | text, timestamps, label scores, audio arrays |
| Vision | `image-classification`, `image-segmentation`, `object-detection`, `depth-estimation`, `keypoint-matching`, `mask-generation`, `zero-shot-image-classification`, `zero-shot-object-detection`, `video-classification` | image/video paths, URLs, PIL images, arrays, candidate labels | labels/scores, boxes, masks, depth maps, keypoints |
| Multimodal | `document-question-answering`, `visual-question-answering`, `image-to-text`, `image-text-to-text`, `image-feature-extraction`, `feature-extraction`, `any-to-any` | combined image/text/audio/video fields | answers, generated text, embeddings, modality-specific outputs |

Aliases such as `sentiment-analysis` and `ner` are convenient but canonical task ids are clearer in reusable code.

## AutoClass Inference Alternative

Use AutoClass APIs when Pipeline hides too much control:

```python
from transformers import AutoConfig, AutoTokenizer, AutoModelForSequenceClassification

config = AutoConfig.from_pretrained(model_id_or_path, local_files_only=True)
tokenizer = AutoTokenizer.from_pretrained(model_id_or_path, use_fast=True, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(model_id_or_path)
inputs = tokenizer("validate the shape", return_tensors="pt")
outputs = model(**inputs)
```

AutoClass is better when you need:

- direct tensor outputs, hidden states, attentions, or logits;
- custom postprocessing or model heads;
- manual batching/collation;
- strict offline loading of all components before constructing an inference path;
- generation control through `GenerationConfig`, `generate()`, `TextIteratorStreamer`, or custom decoding.

For chat and token-level generation details, use the sibling `generation` sub-skill.

## Source and Cache Choices

| Need | Recommended options | Validation |
| --- | --- | --- |
| Reproducible Hub load | `model="org/name"`, `revision="commit-or-tag"` | print resolved `pipe.model.config.name_or_path`; pin revision in configs |
| Offline local run | `model="./model-dir"`, `local_files_only=True` | run `AutoConfig.from_pretrained(path, local_files_only=True)` first |
| Private/gated model | `token=True` or environment-managed auth | verify auth outside code; avoid logging token values |
| Custom model code | `trust_remote_code=True` only after review | inspect model repo code and prefer pinned revisions |
| Separate components | pass explicit `tokenizer=`, `processor=`, `image_processor=`, etc. | assert component class names and sample output shape |

## Device and Dtype Decisions

| Environment | Constructor choice | Notes |
| --- | --- | --- |
| Generic CPU | omit `device` or use `device=-1`; keep `dtype="auto"` | most portable; batching rarely helps |
| Single CUDA GPU | `device=0`; consider `dtype="float16"` | check `torch.cuda.is_available()` and memory |
| Multiple devices / large model | `device_map="auto"`; often pair with `dtype="auto"` or `"bfloat16"` | requires Accelerate-style placement; do not also pass `device` |
| Apple Silicon | `device="mps"` | dtype support varies; fall back to CPU for unsupported ops |
| Quantized model | pass `model_kwargs={"quantization_config": ...}` and often `device_map="auto"` | route detailed quantization decisions to `quantization-integrations` |

Avoid these conflicts:

```python
# Bad: top-level and model_kwargs conflict.
pipeline("text-generation", model=model_id, dtype="float16", model_kwargs={"dtype": "float16"})

# Bad: device and device_map fight over placement.
pipeline("text-generation", model=model_id, device=0, device_map="auto")
```

## Input and Output Shape Checks

Use task-specific assertions in smoke tests and application boundaries:

```python
result = pipe(sample)
assert result is not None
if task in {"text-classification", "image-classification", "audio-classification", "video-classification"}:
    assert isinstance(result, list) and isinstance(result[0], dict)
    assert {"label", "score"} <= set(result[0])
elif task == "automatic-speech-recognition":
    assert isinstance(result, dict) and "text" in result
elif task == "text-generation":
    assert isinstance(result, list) and "generated_text" in result[0]
```

Batching can change nesting. A single string for text generation usually returns `list[dict]`; a list of strings may return `list[list[dict]]` for generation-style tasks. Normalize around your application boundary instead of assuming all tasks use one shape.

## Task-Specific Call Options

Examples of call-time options:

- ASR: `return_timestamps=True` or task-supported timestamp modes.
- Text generation: `max_new_tokens`, `return_full_text=False`, `num_return_sequences`; route advanced behavior to `generation`.
- Token classification: aggregation options affect entity grouping.
- Zero-shot classification: candidate labels and hypothesis template drive output semantics.
- Vision/detection: `threshold`, `top_k`, and image argument names differ by task.
- Batching: `batch_size=...`, `truncation=...`, and dataset/generator inputs are call-time choices.

## Custom Pipeline Class

Use `pipeline_class=...` only when the workflow owns a custom `Pipeline` subclass and needs custom preprocessing/forward/postprocessing. For reusable public skills, prefer built-in tasks unless model extension is the actual objective; route custom registration and architecture work to `model-extension`.
