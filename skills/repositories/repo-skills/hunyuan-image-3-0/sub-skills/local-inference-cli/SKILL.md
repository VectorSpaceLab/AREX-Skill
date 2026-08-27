---
name: local-inference-cli
description: "Use HunyuanImage-3.0's local generation CLI and reference demo
  recipes for safe T2I, TI2I, instruct, and distil command building."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Local Inference CLI

Use this sub-skill when the task is about local image generation with the bundled runner, or when a user wants a safe command render before touching a GPU run.

## Read first

- [CLI reference](references/cli-reference.md) for the full flag matrix, checkpoint naming rules, and the actual entry surfaces.
- [Workflow recipes](references/workflows.md) for base, instruct, distil, multi-image, reproduction, and Taylor Cache recipes.
- [Troubleshooting](references/troubleshooting.md) for missing model paths, malformed flags, optional accelerator warnings, and the broken console-script fallback.
- [Skill-owned generation runner](scripts/run_hunyuan_image_generation.py) for self-contained execution against an installed package and local checkpoint.
- [Dry-run command renderer](scripts/local_inference_cli_dry_run.py) to render or validate a command without importing the model stack or launching generation.

## Covers

- Local checkpoint selection for base, instruct, and distil runs.
- Local generation flags for prompt, image, seed, save path, image sizing, task selection, system prompts, reproduction, and Taylor Cache.
- Single-image and multi-image TI2I flows, including `think_recaption`, `recaption`, and `infer_align_image_size`.
- Safe command rendering and validation, including rewrite-branch warnings before any generation starts.
- Distilled demo shell recipes as reference-only command templates.

## Does not cover

- Model architecture, tokenizer internals, or public API signatures; route those to `core-apis-and-architecture`.
- System-prompt design, DeepSeek prompt rewriting, or prompt semantics beyond the local CLI warning branch; route those to `prompt-and-image-conditioning`.
- vLLM serving or client payload construction.
- Gradio launch details, except to note that the current app launcher is stale.

## Use this sub-skill when

- A user asks for the exact local generation command to run next.
- A user wants to compare base, instruct, and distil checkpoint recipes.
- A user needs to sanity-check generation flags before downloading weights or starting GPU work.
- A user wants a safe dry-run of a multi-image TI2I or rewrite-oriented recipe.
