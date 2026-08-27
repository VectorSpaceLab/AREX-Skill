---
name: core-components
description: "Reusable Pyramid-Flow model APIs, Causal Video VAE, diffusion
  schedulers, and distributed helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pyramid-Flow Core Components

Use this sub-skill when the task is about Pyramid-Flow's reusable runtime building blocks rather than an end-to-end workflow launcher.

## Route here for

- `PyramidDiTForVideoGeneration` construction, component relationships, text-to-video/image-to-video method signatures, latent decoding, VAE tiling, and CPU offload API semantics.
- `CausalVideoVAE` and `CausalVideoVAELossWrapper` encode/decode/reconstruct APIs, latent shapes, and safe tiny round-trip checks.
- `PyramidFlowMatchEulerDiscreteScheduler` and `DDPMCosineScheduler` initialization, timestep setup, and `step()` semantics.
- `trainer_misc` distributed helpers shared by inference and training: rank/world-size helpers, DDP initialization, sequence-parallel groups, sync-input groups, and FSDP epoch helper entry points.

## Route elsewhere

- Generation demo launchers, Gradio apps, prompt/image recipes, checkpoint download commands, and multi-GPU generation wrappers -> `generation-inference`.
- JSONL annotations, dataset fixtures, text-feature extraction, and VAE-latent precompute flows -> `data-preparation`.
- Training shell launchers, CLI flag catalogs, AR/non-AR DiT fine-tuning recipes, and VAE training recipes -> `training-workflows`.

## Bundled references

- [API reference](references/api-reference.md) has verified signatures, imports, scheduler/VAE smoke facts, dependency versions, and shape contracts.
- [Model overview](references/model-overview.md) explains how DiT, text encoders, VAE, schedulers, and distributed helpers fit together.
- [Troubleshooting](references/troubleshooting.md) covers dependency drift, CUDA visibility, scheduler stage errors, VAE shape/device misuse, and invalid model paths or variants.

## Bundled script

Run the safe component smoke from any working directory once Pyramid-Flow's import roots are importable in the active Python environment:

```bash
python PATH_TO_SKILL_TREE/sub-skills/core-components/scripts/smoke_core_components.py --help
python PATH_TO_SKILL_TREE/sub-skills/core-components/scripts/smoke_core_components.py --package-root PATH_TO_PYRAMID_FLOW
```

The smoke checks imports, package versions, scheduler CPU math, a tiny CPU Causal Video VAE encode/decode round-trip, and optional negative cases without downloading checkpoints or launching generation/training.
