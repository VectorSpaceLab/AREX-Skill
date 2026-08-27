---
name: generation-inference
description: "Route Pyramid-Flow generation workflows, Gradio demos, notebook
  recipes, and multi-GPU inference launchers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generation Inference

Use this sub-skill when the user asks how to run, adapt, validate, or troubleshoot Pyramid-Flow generation and demo workflows.

## Owns

- Text-to-video generation from prompts.
- Image-to-video generation from a prompt plus an input image.
- The text-to-image/image variant recipe.
- Single-process Gradio demo behavior and the multi-GPU Gradio front end.
- Multi-GPU inference command semantics, sequence-parallel launch requirements, prompt/image inputs, output video export, CPU offload choices, and MPS caveats.

## Route elsewhere

- Dataset annotation, dataset loading, text-feature extraction, or VAE-latent precompute flows: use `data-preparation`.
- Causal VAE training, Pyramid-Flow DiT training, FSDP, training configs, or long fine-tuning launchers: use `training-workflows`.
- Low-level `PyramidDiTForVideoGeneration` internals, scheduler details, VAE internals, tensor-shape contracts, or reusable component APIs: use `core-components`.

## Runtime references

- Start with [references/workflows.md](references/workflows.md) for workflow selection, model/variant choices, direct recipes, and multi-GPU launch shapes.
- Use [references/gradio-and-api-inference.md](references/gradio-and-api-inference.md) for distilled behavior of the Gradio demos, notebooks, API signatures, prompt/image inputs, and output export.
- Use [references/troubleshooting.md](references/troubleshooting.md) for checkpoint/download failures, model/variant mismatches, CUDA OOM, CPU offload, sequence-parallel world-size mismatches, missing `image_path`, and Gradio/Hugging Face cache issues.

## Bundled scripts

- `scripts/check_generation_prereqs.py` validates checkpoint layout, model/variant compatibility, image-to-video inputs, CUDA/MPS visibility, and sequence-parallel GPU counts without importing the side-effectful demo apps.
- `scripts/run_generation.py` is a safe-by-default command planner and optional execution wrapper distilled from the repository launchers. By default it prints the command that would run; pass `--execute` or `--launch` only when a real checkpoint, importable Pyramid-Flow package, and required backend are ready.

## Safety defaults

- Do not import the original Gradio apps during inspection: the single-GPU app downloads model files at import time.
- Validate `pyramid_flux`/`pyramid_mmdit`, `384p`/`768p`, and image-variant combinations before launching.
- Reject image-to-video requests without a readable input image.
- Treat multi-GPU generation as CUDA + `torchrun` + `world_size == sp_group_size`; sequence parallelism is not a CPU/MPS fallback.
