---
name: reduced_recovery_harness
description: Build executable soft-mode LDM proxy recovery artifacts from generated skills with mechanism checks and validator evidence.
---

# Reduced Recovery Harness

Use this skill when full Latent Diffusion Model checkpoints or datasets are unavailable in a bounded run and soft-mode recovery permits a declared proxy. It coordinates generated skill scripts, writes recovery artifacts, and prepares evidence for the Distiller recovery validator. Do not use it in hard mode as accepted success.

## Inputs

- Attempt directory containing `module_plan.json`.
- Runtime handoff path from environment preparation.
- Generated skills root containing compression, objective, conditioning, and spatial scripts.
- Optional resource provenance for a synthetic or resource-derived image item.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json` and command evidence produced by the caller.

## Workflow

1. Read the module-plan target and runtime blockers.
2. Declare whether the experiment is reduced/proxy and why full recovery is blocked.
3. Invoke the generated module scripts instead of duplicating their logic silently.
4. Combine their outputs into mechanism checks for compression, latent noising, cross-attention, spatial planning, and optimizer execution.
5. Write validation-compatible artifacts and keep the original source repository out of recovery sources.

## Validation

Run `python scripts/build_proxy_result.py --attempt-dir <attempt> --skills-root <generated_skills_root> --runtime-handoff <attempt>/environment/runtime_handoff.json`. Then run the Distiller recovery validator on the attempt directory.

## Limitations

The harness produces a reduced mechanism proxy, not a published FID reproduction. It depends on the generated module scripts and must be rerun after skill refinements.
