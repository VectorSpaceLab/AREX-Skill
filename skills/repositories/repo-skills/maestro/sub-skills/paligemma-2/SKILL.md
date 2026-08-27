---
name: paligemma-2
description: "Use Maestro's PaliGemma 2 recipe for JSON extraction, VQA,
  OCR-style fine-tuning, checkpoint loading, and inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaliGemma 2

Use this sub-skill when the user needs Maestro's `paligemma_2` route for PaliGemma 2 text-generation fine-tuning or inference over images: JSON extraction, VQA, OCR-style prompts, loading/saving checkpoints, or choosing LoRA/QLoRA/freeze/full fine-tuning behavior.

## Route here for

- CLI training through `maestro paligemma_2 train`.
- Python training through `maestro.trainer.models.paligemma_2.core.PaliGemma2Configuration` and `train(config)`.
- Checkpoint work through `load_model(...)`, `save_model(...)`, and `OptimizationStrategy`.
- Single-image prediction through `maestro.trainer.models.paligemma_2.inference.predict(...)`.
- PaliGemma-specific prompt handling, especially when and where Maestro prepends `<image>`.

## Route elsewhere

- Generic JSONL split validation, Roboflow dataset identifiers, image-file checks, and metric registry details belong in [datasets-and-metrics](../datasets-and-metrics/).
- Florence-2 or Qwen2.5-VL detection formatting belongs in their sibling sub-skills. Maestro's PaliGemma 2 implementation provides train/evaluation collate functions and text prediction; it does **not** expose a PaliGemma object-detection formatter API.
- Package-wide installation, root CLI discovery, and non-model-specific import warnings belong in the root [installation and CLI guide](../../references/installation-and-cli.md) and root troubleshooting reference.

## Source-backed defaults to preserve

- Default model id: `google/paligemma2-3b-pt-224`.
- Default revision: `refs/heads/main`.
- Default train output base: `./training/paligemma_2`; training creates a numbered run directory below it.
- Training/evaluation generation length default: `PaliGemma2Configuration.max_new_tokens = 512`.
- Direct prediction default: `predict(..., max_new_tokens=1024)`.
- Dataset JSONL `prefix` values should not include `<image>` for standard Maestro use; `train_collate_fn`, `evaluation_collate_fn`, and `predict` prepend `<image>` internally.

## Operating sequence

1. Confirm the dataset task and split layout with [datasets-and-metrics](../datasets-and-metrics/) before choosing model parameters.
2. Use [API reference](references/api-reference.md) to choose CLI vs Python API, optimization strategy, checkpoint load/save behavior, and exact option names.
3. Use [workflows](references/workflows.md) for JSON extraction, VQA, OCR-style fine-tuning, inference, and safe validation steps.
4. Use [troubleshooting](references/troubleshooting.md) for QLoRA/bitsandbytes, CUDA memory, invalid JSON suffixes, token truncation, HF access, and CLI edge cases.
5. Use the bundled helper only to generate configuration text; it never downloads models or starts training:

```bash
python scripts/build_paligemma_config.py \
  --dataset ./dataset \
  --optimization-strategy lora \
  --metric edit_distance \
  --metric bleu \
  --emit json
```
