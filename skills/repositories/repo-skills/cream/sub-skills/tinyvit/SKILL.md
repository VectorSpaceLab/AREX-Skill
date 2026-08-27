---
name: tinyvit
description: "Routes TinyViT model creation, evaluation, sparse-logit saving,
  finetuning, and training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TinyViT

Use this sub-skill when the user is working with TinyViT model families, ImageNet-22k sparse-logit distillation, or the 22k-to-1k / higher-resolution finetuning paths.

## What this route owns

- TinyViT model variants and their known input sizes.
- ImageNet-1k evaluation and training.
- ImageNet-22k sparse-logit saving and checking.
- 22k-to-1k finetuning and higher-resolution finetuning.
- The small helper commands that inspect known variant metadata and print safe launcher templates.

## When to use it

Choose this route for prompts like:

- "evaluate TinyViT"
- "save teacher logits"
- "finetune TinyViT from 22k to 1k"
- "check the TinyViT 384 or 512 variant"
- "fix a TinyViT config or checkpoint mismatch"

## What to read next

- `references/api-reference.md` for the verified model variants, config keys, and expected shapes.
- `references/workflows.md` for the launcher templates.
- `references/troubleshooting.md` for dataset, config, checkpoint, and distillation issues.
- `scripts/inspect_tinyvit_models.py` to print the known variant metadata without requiring the original source code.
- `scripts/build_tinyvit_command.py` to print safe launcher templates.

## Important boundaries

- Do not route TinyCLIP, MiniViT, EfficientViT, AutoFormer, or iRPE-only tasks here.
- Keep the generated helper scripts self-contained; do not depend on the original repository checkout for their runtime behavior.
- The inspection helper is a metadata checker, not a model-training entry point.

## Working pattern

1. Identify the target variant or workflow stage.
2. Read the API reference to confirm the config file and dataset expectations.
3. Use the metadata inspector to confirm the variant name and expected input size.
4. Use the command builder to print the exact command template for the requested stage.

## Common signals

- `tiny_vit_5m_224`, `tiny_vit_11m_224`, `tiny_vit_21m_224`, `tiny_vit_21m_384`, and `tiny_vit_21m_512` are the main variants.
- `DATA.DEBUG True` is useful for fast sparse-logit or dataset checks.
- `DISTILL.TEACHER_LOGITS_PATH` must be set when running the distillation path.
- `ImageNet-22k` and `ImageNet-1k` layouts are both used in the full workflow.
