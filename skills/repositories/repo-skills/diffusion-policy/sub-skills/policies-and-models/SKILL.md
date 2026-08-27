---
name: policies-and-models
description: "Choose and inspect policy and model families, interface contracts,
  checkpoints, and normalization behavior for diffusion-policy."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Policies and Models

Use this sub-skill when you need to choose a policy family, inspect its inference API, load or compare checkpoints, or debug model-level import and shape issues.

## Covers
- Base low-dim and image policy contracts
- Diffusion UNet and Transformer backbones
- Low-dim, image, hybrid, Robomimic, BET, and IBC policy families
- Normalizers and checkpoint-loaded model state
- Model-specific troubleshooting for optional dependencies and device mismatches

## Route elsewhere
- Dataset construction, ReplayBuffer, and sampling windows -> `../data-and-replay-buffers/`
- Training, evaluation, multirun, and benchmark orchestration -> `../training-and-evaluation/`
- Real camera or robot acquisition and actuation -> `../real-robot-operations/`

## Start here
1. Read `references/policies-and-models.md` for family selection and config examples.
2. Read `references/api-reference.md` for signatures, shapes, and notable methods.
3. Read `references/troubleshooting.md` for common failure modes and checks.
4. Run `scripts/inspect_policy_interfaces.py` to print representative class signatures when optional dependencies are installed.

## Usage hints
- Always match the policy family to the observation structure: vector-only, image-only, mixed image+vector, Robomimic wrapper, discrete latent baseline, or energy-based baseline.
- Treat `shape_meta`, `horizon`, `n_obs_steps`, and `n_action_steps` as the first thing to verify before touching model code.
- If a constructor import fails, treat it as a dependency or optional-backend issue rather than a model bug until the troubleshooting checklist says otherwise.
