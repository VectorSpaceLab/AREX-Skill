---
name: tinyclip
description: "Routes TinyCLIP OpenCLIP-style model inspection, zero-shot
  evaluation, and weight-inheritance pretraining workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TinyCLIP

Use this sub-skill when the user is working with TinyCLIP model configs, inference, evaluation, or pretraining.
It covers the OpenCLIP-style Python API and the stage-based training / evaluation commands documented in the repo.

## What this route owns

- Model config discovery and model/tokenizer construction through `open_clip`.
- Zero-shot ImageNet evaluation and inference-style workflows.
- Manual and auto weight-inheritance pretraining stage commands.

## When to use it

Choose this route for prompts like:

- "inspect TinyCLIP model configs"
- "run TinyCLIP zero-shot evaluation"
- "build the inference command for TinyCLIP"
- "prepare TinyCLIP pretraining stages"
- "fix a TinyCLIP open_clip import or checkpoint issue"

## What to read next

- `references/api-reference.md` for the verified `open_clip` API surface.
- `references/workflows.md` for inference, evaluation, and pretraining command shapes.
- `references/troubleshooting.md` for install, checkpoint, data-loader, and distributed issues.
- `scripts/inspect_tinyclip_models.py` to list TinyCLIP model configs or instantiate one through `open_clip`.
- `scripts/build_tinyclip_command.py` to print safe launcher templates.

## Important boundaries

- Do not route TinyViT, MiniViT, EfficientViT, or generic vision-only CLIP-style tasks here.
- Treat the original stage shell scripts as documentation for the workflow, not as runtime dependencies.
- Keep references self-contained; do not point back to the source checkout for model configs or stage notes.

## Working pattern

1. Determine whether the user wants inference / evaluation or a pretraining stage.
2. Read the API reference for the `open_clip` constructors and model-config names.
3. Use the inspection script when you need to list configs or verify that a model can be instantiated.
4. Use the command-builder script when the user wants a reproducible launcher string.

## Common signals

- `open_clip` is the import name for the installed `open_clip_torch` distribution.
- `TinyCLIP-...` model names are provided by the JSON configs under `src/open_clip/model_configs/`.
- The zero-shot path uses `src/training/main_for_test.py` with `--imagenet-val`, `--model`, `--eval`, and `--resume`.
