---
name: generation
description: "Route waveform diffusion generator, text-conditioning, sampling,
  inpainting, and DiffusionAR tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generation

Use this sub-skill when a request is about:
- building or smoke-checking an unconditional audio diffusion generator,
- sampling with `DiffusionModel.sample`,
- enabling text conditioning with classifier-free guidance,
- filling masked waveform gaps with `VInpainter`,
- or handling the exported but expert-only `DiffusionAR` path.

Route elsewhere:
- upsampling, vocoding, and autoencoding belong in `../conditioning/`.
- pretrained checkpoints, full training runs, benchmark sweeps, and paper-specific recipes are not part of this sub-skill.
- release and import workflows belong to the repo-level skill, not this route.

## Quick workflow

1. Start with `scripts/tiny_generation_smoke.py` for a CPU-only, no-pretrained-weights check.
2. Use `references/api-reference.md` to confirm constructor names, argument rules, and route behavior.
3. Use `references/workflows.md` for the smallest working shapes and expected signals.
4. Use `references/troubleshooting.md` when you hit channel, mask, text-conditioning, or step/schedule errors.

## Owned capabilities

- `DiffusionModel.forward` loss route and `DiffusionModel.sample` sampler route.
- `UNetV0` construction, length checks, attention and cross-attention flags, text-conditioning flags, and `resnet_groups` constraints.
- `VDiffusion`, `UniformDistribution`, `LinearSchedule`, and `VSampler`.
- `VInpainter` source/mask/noise resampling flow.
- Expert notes for `DiffusionAR`.

## Bundled files

- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/tiny_generation_smoke.py`
