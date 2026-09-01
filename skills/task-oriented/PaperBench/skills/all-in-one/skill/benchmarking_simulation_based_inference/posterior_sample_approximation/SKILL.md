---
name: posterior_sample_approximation
description: Fit compact posterior approximations from SBI simulator pairs and emit posterior samples with optimizer traces.
---

# Posterior Sample Approximation

Use this skill when an SBI recovery needs approximate posterior samples from simulation pairs and a fixed observation. It is designed for bounded reduced experiments where a full neural density estimator is unavailable, but the run must still perform an actual optimizer step and return posterior samples.

Do not use this skill as a substitute for a full neural SBI algorithm when that runtime is available. It is a reduced mechanism-preserving approximation.

## Inputs

- Simulation JSON with `theta` and `x` arrays.
- Conditioning observation vector.
- Training settings: learning rate, number of steps, seed.
- Posterior sampling settings: sample count and sample variance.

## Outputs

- Approximate posterior sample JSON.
- Training trace with before/after loss and before/after trainable parameters.

## Workflow

1. Load simulator pairs created by the task protocol skill.
2. Fit an affine map from observations to parameter means with gradient descent.
3. Record `loss_before`, `loss_after`, `params_before`, `params_after`, and `optimizer_state_changed`.
4. Condition the fitted map on the target observation.
5. Draw approximate posterior samples around the predicted mean.
6. Save the sample file and training trace for the recovery validator.

## Validation

Run:

```bash
python scripts/posterior_sample_approximation.py self-test
python tests/test_posterior_sample_approximation.py
```

## Limitations

This script implements a small affine posterior mean model with diagonal Gaussian sampling noise. It demonstrates the benchmark mechanism and optimizer evidence, but it is not a normalizing-flow posterior estimator.

The `optimizer_state_changed` flag is evidence-bearing: a zero-step or otherwise frozen run must leave it `false`, with identical `params_before` and `params_after`.
