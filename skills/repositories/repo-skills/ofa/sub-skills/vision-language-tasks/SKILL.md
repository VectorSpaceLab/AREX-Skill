---
name: vision-language-tasks
description: "Guides OFA captioning, VQA, RefCOCO, SNLI-VE, OCR, and ImageNet
  finetuning and evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# vision-language-tasks

Use this sub-skill when the user wants to run or adapt OFA's main multimodal understanding workflows: captioning, VQA, visual grounding, visual entailment, OCR, or ImageNet classification.

## Trigger phrases

- "Run OFA captioning"
- "VQA beam search or all-candidate eval"
- "RefCOCO training or evaluation"
- "SNLI-VE / visual entailment"
- "OCR or Chinese OCR"
- "ImageNet classification with OFA"

## What this sub-skill owns

- caption finetuning and COCO evaluation,
- VQA constrained / all-candidate / beam / zero-shot routes,
- RefCOCO, RefCOCO+, and RefCOCOg workflows,
- SNLI-VE workflows,
- OCR and ImageNet workflows,
- task-specific selected-column and checkpoint guidance.

## What it excludes

- text-to-image generation -> `image-generation`,
- Gigaword and GLUE -> `language-tasks`,
- pretraining -> `pretraining`,
- generic launch mechanics -> `setup-and-command-building`.

## Read these files

- [references/workflows.md](references/workflows.md) for the end-to-end workflow shapes.
- [references/task-reference.md](references/task-reference.md) for task-specific columns, checkpoints, and metrics.
- [references/troubleshooting.md](references/troubleshooting.md) for common workflow failures.
- [scripts/coco_caption_eval.py](scripts/coco_caption_eval.py) for COCO caption metric evaluation.

## Typical workflow

1. Identify the task family and split.
2. Confirm the correct `selected_cols` and checkpoint.
3. Validate the input file with `data-formats` when the row shape is uncertain.
4. Render the command or read the recipe for the exact launch shape.
5. Use the adapted metric helper if the workflow needs offline scoring.

## Notes

- The task family usually determines the selected columns.
- Many commands differ only by the task name and the checkpoint path.
- VQA has multiple evaluation modes; choose beam or all-candidate explicitly.
