---
name: gaussian_mixture_recovery
description: Run a bounded 1D Gaussian-mixture KSD-U recovery experiment for the Kernelized Stein Discrepancy paper.
---

# Gaussian Mixture Recovery Harness

Use this skill to create a fast, mechanism-faithful proxy recovery for the KSD goodness-of-fit paper. It constructs the paper's 1D Gaussian-mixture setting, evaluates a null model and a mean-perturbed model using KSD-U, and reports a recovery metric based on the rejection-rate gap.

Do not use this skill as a full reproduction of every Figure 1 baseline; it intentionally omits likelihood-ratio, MMD, classical CDF tests, and RBM experiments to keep recovery bounded.

## Inputs

- Generated `stein_kernel_scoring` skill directory.
- Generated `ksd_bootstrap_gof` skill directory.
- Experiment parameters: sample size, trial count, bootstrap count, perturbation magnitude, alpha, and seed.
- Optional output path for recovery-compatible JSON.

## Outputs

- Trial-level null and alternative decisions.
- Aggregate null and alternative rejection rates.
- `alternative_rejection_rate_minus_null_rejection_rate` metric.
- Mechanism checks proving score-only model access, RBF Stein kernel use, U-statistic use, centered bootstrap use, and generated skill invocation.

## Workflow

1. Define a fixed five-component 1D Gaussian mixture with equal weights and shared variance.
2. Generate samples from the true mixture for every trial.
3. Evaluate null trials with the true mixture score and alternative trials with a perturbed model score.
4. Compute the pairwise Stein matrix using `stein_kernel_scoring`.
5. Calibrate each test using `ksd_bootstrap_gof`.
6. Aggregate rejection rates and emit recovery-result-compatible JSON.

## Validation

Run:

```bash
python tests/test_gaussian_mixture_recovery.py
```

The tests check mixture score behavior and a tiny end-to-end recovery smoke run.

## Limitations

- This is a declared reduced/proxy recovery target.
- The result is seed- and budget-dependent and should be interpreted as mechanism evidence, not an exact paper-figure value.
- It does not require or read an original source repository.

## Refinement Guards

Refinement guard: perturbation zero is a null-control edge case. The alternative and null scores coincide, so the rejection-rate gap should remain near zero and must not be reported as a successful sample-quality recovery.
