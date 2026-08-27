---
name: diffusion-and-generative
description: "Use PhysicsNeMo diffusion APIs and generative-domain workflows
  without assuming bundled weights or data."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# PhysicsNeMo Diffusion and Generative Workflows

Use this sub-skill when the user asks about PhysicsNeMo diffusion models, denoisers, predictors, preconditioners, noise schedulers, samplers, guidance, multi-diffusion/patching, CorrDiff/StormCast-style weather diffusion, CFD flow reconstruction diffusion, full-waveform inversion diffusion, TopoDiff, SongUNet, DhariwalUNet, StormCastUNet, DiT, or diffusion-specific losses.

## First decide: API building block or full example workflow?

- **API building block**: the user needs imports, signatures, a minimal adapter, a custom scheduler/solver, a tiny sampler smoke, or a loss/preconditioner explanation. Read `references/api-reference.md` and run `scripts/diffusion_api_smoke.py` if an environment check is useful.
- **Full domain workflow**: the user needs to train/generate with weather, CFD, geophysics, or topology-optimization examples. Read `references/diffusion-workflows.md` first, then route data preparation to `../datapipes/SKILL.md`, model-family ambiguity to `../model-selection/SKILL.md`, and multi-GPU/domain-parallel scaling to `../distributed-and-domain-parallel/SKILL.md`.
- **Failure diagnosis**: if the issue includes missing checkpoints, data paths, shape/channel mismatches, sigma/scheduler settings, patch fusion, guidance gradients, CUDA/FP16, or domain-parallel behavior, read `references/troubleshooting.md` before changing code.

## Quick workflow

1. Clarify the task target: training loss, sampling/inference, conditioning/guidance, patching, or a domain recipe.
2. State explicitly whether the user has the required **trained weights/checkpoints**, **datasets/statistics**, and **example-specific optional dependencies**. PhysicsNeMo does not bundle pretrained domain weights or external datasets with this generated skill.
3. For core API work, assemble the pipeline in this order: `DiffusionModel`/adapter -> optional preconditioner -> noise scheduler -> loss for training, or predictor -> scheduler `get_denoiser` -> solver/sample for inference.
4. For domain workflows, separate safe API smokes from real training/generation. Real CorrDiff, StormCast, CFD, FWI, and TopoDiff runs require user-provided data, checkpoints or long training, and usually CUDA.
5. For large spatial domains, choose between patch-based multi-diffusion and domain parallelism. Use multi-diffusion for patching a 2D field inside the diffusion stack; route `ShardTensor` and launch details to `../distributed-and-domain-parallel/SKILL.md`.
6. Prefer tiny local validation before expensive work: run `python scripts/diffusion_api_smoke.py --tiny-sampling` from this sub-skill directory, then only run user-authorized full workflow commands after the required data, checkpoints, dependencies, and backend are confirmed.

## Do not do these by default

- Do not imply pretrained weights, CorrDiff/StormCast/TopoDiff datasets, NGC resources, Figshare files, Dropbox files, or FWI data are bundled.
- Do not run training, dataset downloads, external authentication, model checkpoint downloads, or multi-hour generation as a smoke test.
- Do not treat source repository examples or tests as runtime dependencies. This sub-skill distills their behavior into bundled references and a safe script.
- Do not use `torch.inference_mode()` around DPS-style guidance that needs gradients; use the troubleshooting reference for the safe autograd pattern.
