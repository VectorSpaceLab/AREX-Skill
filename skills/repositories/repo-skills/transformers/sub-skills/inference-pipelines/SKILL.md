---
name: inference-pipelines
description: "Use Transformers pipelines and AutoClass inference workflows
  across text, vision, audio, video, and multimodal tasks, with safe device,
  dtype, batching, offline, and validation choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference Pipelines

Use this sub-skill when an agent needs high-level inference with `transformers.pipeline()` or needs to decide whether a Pipeline, AutoClass call, or lower-level generation workflow is the right fit.

## Start Here

- Choose Pipeline for standard inference tasks where Transformers owns preprocessing, model forwarding, and postprocessing.
- Choose AutoClass inference when the task needs custom tensor logic, custom preprocessing, or nonstandard outputs not exposed by a task pipeline.
- Choose the sibling [generation](../generation/SKILL.md) sub-skill when the main challenge is chat templating, `generate()`, streamers, decoding, generation config, or token-level control.
- Choose the sibling [tokenizers-processors](../tokenizers-processors/SKILL.md) sub-skill when the main challenge is tokenizer/processor loading, padding/truncation, chat templates, image/audio processors, or multimodal preprocessing.
- Choose the sibling [serving-cli](../serving-cli/SKILL.md) sub-skill for CLI, server, deployment, or command-entrypoint workflows.
- Choose the sibling [quantization-integrations](../quantization-integrations/SKILL.md) sub-skill when memory reduction, bitsandbytes, Accelerate placement, or third-party quantization drives the design.
- Choose the sibling [model-extension](../model-extension/SKILL.md) sub-skill for custom models, new architectures, pipeline registration, or `trust_remote_code` review.

## Core API

The inspected package exposes `transformers.pipeline()` with these important constructor choices:

```python
from transformers import pipeline

pipe = pipeline(
    task="text-classification",
    model="distilbert/distilbert-base-uncased-finetuned-sst-2-english",
    device=-1,
    dtype="auto",
)
print(pipe("Transformers pipelines are convenient."))
```

Key parameters include `task`, `model`, `config`, `tokenizer`, `feature_extractor`, `image_processor`, `video_processor`, `processor`, `revision`, `use_fast`, `token`, `device`, `device_map`, `dtype="auto"`, `trust_remote_code`, `model_kwargs`, `pipeline_class`, and task-specific `**kwargs`.

Use [`references/api-reference.md`](references/api-reference.md) for task families, constructor parameters, expected input/output shapes, AutoClass alternatives, and validation checks.

## Fast Workflow

1. Identify the modality and task: text, image, audio, video, document, or multimodal.
2. Pick a concrete `task` id and model id/local path; avoid relying on default models for reproducible code.
3. Decide model source:
   - Hub id for online examples and normal usage.
   - Local directory for offline, pinned, or private model files.
   - `revision` for reproducible Hub loading.
   - `local_files_only=True` for no-network validation.
4. Decide hardware:
   - CPU: `device=-1` or omit `device`; avoid batching unless measured.
   - One GPU: `device=0`; consider `dtype="float16"` only when supported.
   - Apple Silicon: `device="mps"`; validate dtype support.
   - Automatic multi-device placement: use `device_map="auto"` and do not also set `device`.
5. Build the pipeline and run one tiny representative input.
6. Assert output shape and keys before integrating into application code.
7. Add batching only after correctness is proven and memory behavior is measured.

Use [`references/workflows.md`](references/workflows.md) for complete patterns and copyable snippets.

## Safe Offline Smoke

This sub-skill bundles a dry-run-first helper:

```bash
python sub-skills/inference-pipelines/scripts/pipeline_smoke.py \
  --task text-classification \
  --model ./local-model \
  --local-files-only
```

By default the script imports Transformers, checks task/model arguments, tries `AutoConfig.from_pretrained(..., local_files_only=True)` when a model is provided, and prints construction advice without downloading weights. Add `--run` only when the requested model and optional dependencies are available locally or network access is intended.

## Common Decisions

- Prefer `dtype="auto"` for generic code; use explicit `float16`/`bfloat16` only after confirming the backend and hardware support it.
- Do not pass both `device` and `device_map`; pipeline warns that `device` overrides `device_map` and can produce unexpected behavior.
- Use `model_kwargs={...}` for model-loading options, but do not duplicate `dtype` or `device_map` both top-level and inside `model_kwargs`.
- Use `token=True` or a token string only for private/gated Hub models; never hard-code secrets in skill examples or application code.
- Keep `trust_remote_code=False` unless the model repository code has been reviewed and the workflow explicitly requires it.
- For offline code, set `local_files_only=True` and point `model`, tokenizer, processor, and config arguments to local directories.

## Output Validation

Validate outputs by task rather than assuming one shape:

- Text classification: list of dictionaries with `label` and `score`.
- Text generation: list of dictionaries with `generated_text`; chat inputs may return generated message structures depending on task/model behavior.
- Token classification: token/span dictionaries; aggregation settings affect shape.
- Question answering: dictionary with `answer`, `score`, `start`, and `end` when supported.
- Image/audio/video classification: list of label/score dictionaries.
- Object detection and segmentation: dictionaries can include boxes, masks, labels, and scores.
- ASR: dictionary with `text`, optionally `chunks` when timestamps are requested.
- Feature extraction: nested numeric arrays or tensors depending on options.

## Troubleshooting Routes

Use [`references/troubleshooting.md`](references/troubleshooting.md) when you see:

- Optional dependency errors for PyTorch, torchvision, Pillow, soundfile, librosa, decord, accelerate, or backend packages.
- Hub, network, cache, auth, gated model, or offline failures.
- `device_map`/`device` conflicts or placement warnings.
- dtype failures on CPU, MPS, unsupported GPU, or missing PyTorch.
- Unsupported task/model mismatches, wrong pipeline class, or missing processor/tokenizer files.
- Batch slowdowns, padding explosions, OOM, or list-vs-single output shape surprises.
- `trust_remote_code` prompts or unsafe custom-code requirements.

## Minimal Examples

Text classification:

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = classifier("Skill routing should be explicit.")
assert isinstance(result, list) and {"label", "score"} <= result[0].keys()
```

Image classification:

```python
from transformers import pipeline

classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
result = classifier(images="cat.png")
assert isinstance(result, list) and "score" in result[0]
```

ASR:

```python
from transformers import pipeline

asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")
result = asr(audio="clip.flac", return_timestamps=True)
assert "text" in result
```

Text generation with Pipeline:

```python
from transformers import pipeline

generator = pipeline("text-generation", model="openai-community/gpt2", max_new_tokens=20)
result = generator("A compact smoke test", return_full_text=False)
assert "generated_text" in result[0]
```

For detailed chat/generation trade-offs, route to [generation](../generation/SKILL.md).

## Evidence Base

This sub-skill distills Transformers 5.13.0.dev0 behavior from the README quickstart, quicktour, pipeline API docs, pipeline implementation, and pipeline tests. Runtime guidance is self-contained and does not require opening source files.
