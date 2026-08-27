---
name: model-inference
description: "Use installed otter-ai for Otter, Flamingo, and OtterHD inference,
  YAML batch prompts, Hugging Face loading, and checkpoint conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# model-inference

Use this sub-skill when the task is to run or prepare model inference with the installed `otter-ai` package, load Otter or Flamingo checkpoints through Hugging Face APIs, construct prompt/media tensors, validate YAML batch inference inputs, or plan checkpoint conversion.

## Route here for

- `OtterForConditionalGeneration` or `FlamingoForConditionalGeneration` loading, `forward`, and `generate` calls.
- `OtterConfig` construction or saved-config inspection.
- Otter image/no-image prompts, Flamingo-compatible media conditioning, and OtterHD/Fuyu demo-style prompts.
- YAML batch inference files with `question` and optional `image_path` fields.
- Precision, Flamingo-to-Otter, PT-to-HF, or LoRA checkpoint conversion planning.

## Route away

- Training, finetuning, distributed launch, DeepSpeed, W&B, or checkpoint training cadence: [training](../training/SKILL.md).
- Controller/worker/Gradio serving, long-running web processes, or HTTP endpoint payloads: [serving](../serving/SKILL.md).
- Benchmark dataset/model registries, GPT-judged evaluation, or benchmark configs: [benchmark-evaluation](../benchmark-evaluation/SKILL.md).
- MIMIC-IT data schemas, Convert-It adapters, Syphus instruction generation, or data conversion: [data-preparation](../data-preparation/SKILL.md).

## Operating workflow

1. Classify the task as direct API inference, YAML batch inference, or checkpoint conversion.
2. For direct API inference, read [API reference](references/api-reference.md) for imports, installed signatures, tensor shapes, prompt templates, and generated-output decoding.
3. For YAML batch inference, validate inputs first with [validate_inference_yaml.py](scripts/validate_inference_yaml.py), then follow [workflows](references/workflows.md).
4. For conversion, inspect the safe conversion manifest with [inspect_checkpoint_conversion_args.py](scripts/inspect_checkpoint_conversion_args.py), then follow [conversion](references/conversion.md). The helper does not load checkpoints.
5. If loading or generation fails, use [troubleshooting](references/troubleshooting.md) before changing dependencies, model dtype, device placement, or prompt format.

## Quick reference map

| Need | Start with |
|---|---|
| Import/load Otter or Flamingo model | [API reference](references/api-reference.md#import-and-load-surface) |
| Build `vision_x`, `lang_x`, `attention_mask` | [API reference](references/api-reference.md#prompt-and-media-tensor-contract) |
| Run a YAML batch | [workflows](references/workflows.md#yaml-batch-inference) |
| Validate an inference YAML file | [validate_inference_yaml.py](scripts/validate_inference_yaml.py) |
| Estimate memory/device placement | [workflows](references/workflows.md#memory-and-device-placement-notes) |
| Plan checkpoint conversion | [conversion](references/conversion.md) |
| Diagnose xformers, import, tensor shape, or conversion errors | [troubleshooting](references/troubleshooting.md) |
