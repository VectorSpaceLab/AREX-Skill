---
name: data-and-resources
description: "Routes MiniMind-V resource setup and ALLaVA-style parquet dataset
  validation, including dependencies, tokenizer files, SigLIP2 assets, native
  weights, sample images, and image placeholder semantics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Data and Resources

Use this sub-skill when a user needs to prepare or audit MiniMind-V resources before training, evaluation, serving, or conversion work.

## Triggers

- Checking MiniMind-V dependency expectations, especially data/vision dependencies and torch backend fit.
- Confirming local resource layout for tokenizer files, the SigLIP2 vision encoder, native `.pth` weights, parquet datasets, or image folders.
- Validating an ALLaVA-style MiniMind-V parquet file before training.
- Explaining how `<image>` placeholders become MiniMind-V image tokens.
- Diagnosing missing columns, invalid conversation JSON, unreadable image bytes, missing tokenizer/SigLIP2/model weights, or torch mismatch.

## Route elsewhere

- Model class internals, tensor shapes, projector details, or architecture changes: `model-architecture-and-api`.
- Training commands, distributed launch, checkpoint resume, or optimizer/runtime scheduling: `training`.
- Generation, command-line chat, WebUI, prompt execution, or serving: `inference-and-serving`.
- Native `.pth` to/from Transformers conversion: `model-export-and-format-conversion`.

## Workflow outline

1. Read [resources-and-data](references/resources-and-data.md) for dependencies, resource tree, parquet schema, chat preprocessing, and validation workflow.
2. From a MiniMind-V checkout, verify local resources under relative paths; do not download anything unless the user explicitly approves resource acquisition.
3. For parquet validation, run the bundled [`validate_vlm_parquet.py`](scripts/validate_vlm_parquet.py) helper with the user's parquet path.
4. If validation fails or resources are missing, consult [troubleshooting](references/troubleshooting.md) and report the smallest concrete fix.
5. Hand off to the routed sub-skill if the user then asks to train, infer, serve, inspect model internals, or convert formats.

## Key facts to preserve

- `torch` and `torchvision` are intentionally commented in MiniMind-V requirements and must be installed separately to match the host backend.
- Tokenizer assets live under `model/`; the image token is `<|image_pad|>`.
- The required SigLIP2 vision encoder directory is `model/siglip2-base-p32-256-ve/`.
- Native PyTorch weights normally live under `out/`; dataset parquet files live under `dataset/`.
- MiniMind-V parquet rows require `conversations` and `image_bytes`; conversations may be a JSON string or a list, and image bytes may be one binary object or a list of binary objects.
