---
name: reduced_recovery_harness
description: Run a bounded DDPM proxy experiment that exercises generated schedule, epsilon-loss, and reverse-step skills.
---

# Reduced Recovery Harness

Use this skill when full DDPM image training is blocked by runtime limits but soft-mode recovery permits a declared mechanism-faithful proxy. The harness must import or call the generated DDPM module skills rather than duplicating their core equations silently. Do not use it to claim full CIFAR-10 FID or Inception Score reproduction.

## Inputs
- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing `diffusion_schedule`, `epsilon_objective`, and `reverse_denoising_step`.
- Deterministic hyperparameters for a tiny synthetic Gaussian-mixture experiment.

## Outputs
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json` with `params_before` and `params_after`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/source_manifest.json`.
- `recovery/recovery_result.json`.

## Workflow
1. Build a deterministic one-dimensional mixture and fixed Gaussian-noise values.
2. Import the schedule skill and construct `x_t` using closed-form DDPM noising.
3. Train a tiny linear epsilon predictor with gradient descent and record parameter changes.
4. Import the epsilon-objective skill to score loss before and after the optimizer update.
5. Import the reverse-step skill to compute a deterministic denoising mean.
6. Save command-readable JSON artifacts for the recovery validators.

## Validation
Run the harness script, then run:

```bash
python <distiller>/recover-paper/scripts/validate_recovery_experiment.py <attempt_dir> --output <attempt_dir>/recovery/experiment_validation.json
```

A valid soft-mode proxy must report `is_proxy: true`, `reduced_training_executed: true`, `optimizer_step_executed: true`, and `training_step_executed: false`.

## Limitations
The harness validates DDPM mechanism execution on a reduced synthetic dataset. It is not full image generation, does not estimate FID, and must be interpreted as proxy evidence only.
