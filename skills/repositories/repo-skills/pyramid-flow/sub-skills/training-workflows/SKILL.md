---
name: training-workflows
description: "Route Pyramid-Flow Causal VAE training, DiT fine-tuning,
  distributed launchers, and launch-time prerequisites."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pyramid-Flow training workflows

Use this sub-skill when the task is about Pyramid-Flow training launchers or preflight checks, not inference demos or low-level model internals.

## Route here for

- Autoregressive temporal-pyramid DiT video fine-tuning from `train/train_pyramid_flow.py` and `scripts/train_pyramid_flow.sh`.
- Non-AR/full-sequence DiT fine-tuning from `train/train_pyramid_flow.py` and `scripts/train_pyramid_flow_without_ar.sh`.
- Causal Video VAE stage-1 and stage-2 training from `train/train_video_vae.py` and `scripts/train_causal_video_vae.sh`.
- FSDP, sequence-parallel, sync-input, DDP, and VAE context-parallel startup issues.
- Training prerequisites: CUDA GPU count, LPIPS checkpoint, checkpoint/model paths, annotation inputs, `NUM_FRAMES`, `VIDEO_SYNC_GROUP`, `CONTEXT_SIZE`, and per-device batch-size invariants.

## Route elsewhere

- Inference demos, Gradio apps, prompts, generated videos, and generation launchers: `../generation-inference/SKILL.md`.
- Annotation authoring, JSONL schemas, text-feature extraction, and VAE-latent precompute commands: `../data-preparation/SKILL.md`.
- Model API signatures, scheduler math, VAE encode/decode internals, and reusable tensor-shape details: `../core-components/SKILL.md`.

## Read first

1. [CLI reference](references/cli-reference.md) for verified training flags, defaults, helper signatures, and invariants.
2. [Workflows](references/workflows.md) for AR DiT, non-AR DiT, and two-stage Causal VAE launch planning.
3. [Troubleshooting](references/troubleshooting.md) for GPU, LPIPS, FSDP, context-parallel, gradient-checkpointing, resolution, and annotation failures.

## Bundled helpers

- `scripts/build_training_commands.py` prints validated `torchrun` command shapes adapted from the three training shell launchers. It never starts a training run.
- `scripts/check_training_prereqs.py` validates command-builder invariants, CUDA/distributed visibility, optional source syntax, and optional annotation samples before launch. It never launches `torchrun`.

For any expensive run, build or check the command first, fix all preflight failures, then copy the printed command into the actual training environment.
