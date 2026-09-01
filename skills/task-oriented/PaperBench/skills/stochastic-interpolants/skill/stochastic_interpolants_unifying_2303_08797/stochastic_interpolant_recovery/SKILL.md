---
name: stochastic_interpolant_recovery
description: Run a deterministic reduced Gaussian-mixture recovery that exercises stochastic-interpolant construction, objectives, denoising, and sampling evidence.
---

# Stochastic Interpolant Recovery

Use this skill to run a bounded soft-mode proxy for the paper's Gaussian-mixture experiments. It should be used only after the protocol, objectives, and sampler skills exist and have passed validation.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing the three core generated skills.
- Deterministic seed, sample count, optimizer step count, and learning rate.

## Outputs

- `recovery/recovery_result.json` with numeric metrics and mechanism checks.
- `recovery/logs/training_trace.json` with before/after losses and parameters.
- `recovery/logs/generated_data_item.json` describing the synthetic Gaussian-mixture proxy.
- `recovery/logs/generated_skill_invocations.json` proving generated skill usage.

## Workflow

1. Read the module-plan target and declare this as a reduced proxy, not a full Figure 12 reproduction.
2. Build one-dimensional endpoint samples with a standard-normal source and a two-component target mixture.
3. Import the generated protocol/objective/sampler helpers.
4. Fit linear velocity and denoiser predictors with gradient descent on the paper's quadratic objectives.
5. Integrate an ODE sampler using the learned velocity and compute transport progress toward the target mean.
6. Save all recovery logs before running the Distiller recovery validator.

## Validation

Run:

```bash
python scripts/run_reduced_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>
python tests/test_recovery.py
```

## Limitations

This is a reduced proxy suitable for soft mode when full neural Gaussian-mixture/image recovery is blocked by runtime bounds. It must not be reported as a full paper reproduction.
