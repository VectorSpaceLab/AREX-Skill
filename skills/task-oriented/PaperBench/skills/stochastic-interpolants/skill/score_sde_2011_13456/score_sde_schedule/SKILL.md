---
name: score_sde_schedule
description: Define continuous-time score-SDE schedules, perturbation kernels, reverse drifts, and probability-flow checks for recovery experiments.
---

# Score SDE Schedule

Use this skill when a recovery or implementation task needs the paper's continuous-time forward perturbation and reverse-dynamics contracts without depending on the original repository. It is appropriate for VE-style reduced experiments, formula cross-checks, and small deterministic tests. Do not use it as evidence that full image-model training ran.

## Inputs
- SDE family, currently `ve` for deterministic scripts.
- Scalar or list time values in `[0, 1]`.
- Schedule parameters `sigma_min` and `sigma_max`.
- State and score values when computing reverse or probability-flow drift.

## Outputs
- VE marginal standard deviation and perturbation records.
- Diffusion coefficient `g(t)`.
- Reverse-SDE score drift and probability-flow score drift.
- Validation booleans for factor-of-two consistency.

## Workflow
1. Validate positive schedule parameters and bounded times.
2. Compute log-linear VE `sigma(t)` and diffusion coefficient.
3. Perturb samples using caller-supplied deterministic noise when reproducibility matters.
4. Compute reverse drift as `-g(t)^2 score` and probability-flow drift as `-0.5*g(t)^2 score`.
5. Record formula outputs in recovery artifacts when using this skill for a proxy.

## Validation
Run `python scripts/score_sde_schedule.py --self-test` or validate the tree with `validate_skill_tree.py --run-tests`.

## Limitations
The deterministic script intentionally implements the VE formulas needed for bounded recovery. VP and sub-VP can be added by following the same contract, but this skill should not claim to reproduce full paper metrics by itself.
