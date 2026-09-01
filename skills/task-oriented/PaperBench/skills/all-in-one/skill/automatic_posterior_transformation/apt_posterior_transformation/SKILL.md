---
name: apt_posterior_transformation
description: Compute APT posterior-to-proposal-posterior transformations for Gaussian and finite normalized density settings without importance weighting.
---

# APT Posterior Transformation

Use this skill when a recovery or implementation needs the central APT transformation from a true-posterior estimator `q(theta | x)` to the proposal-posterior density used for proposal-drawn training data. Do not use it for SNPE-B-style importance weighting or SNPE-A-style post-hoc posterior correction.

## Inputs

- Posterior estimate density values or Gaussian parameters.
- Prior density values or Gaussian parameters.
- Proposal density values or Gaussian parameters.
- Optional finite grid or atom scores for normalization checks.

## Outputs

- Gaussian transformed proposal-posterior mean and variance.
- Finite normalized probabilities proportional to `q(theta | x) * proposal(theta) / prior(theta)`.
- Diagnostics for invalid transformed precision, nonfinite scores, or support mismatches.

## Workflow

1. For generic finite points, compute `log_q + log_proposal - log_prior`.
2. Normalize with log-sum-exp to get proposal-posterior probabilities.
3. For Gaussian inputs, compute transformed precision:
   `posterior_precision + proposal_precision - prior_precision`.
4. Compute transformed mean from the transformed natural mean.
5. Reject or flag invalid transforms where precision is not positive.

## Validation

Run:

```bash
python tests/test_transformation.py
```

The tests compare Gaussian closed form against finite-grid normalization and check numerical stability.
They also assert that invalid Gaussian precision is reported rather than converted into a nonsensical variance.

## Limitations

- The script implements scalar Gaussian transforms and finite-score normalization.
- Mixture-of-Gaussians formulas are described in the paper but not fully implemented here because the reduced recovery only needs scalar Gaussian checks.
- This skill provides transformation math; it does not run simulator rounds or optimizer steps.
