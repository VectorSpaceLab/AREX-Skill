---
name: sbi_snpe_training_loop
description: Run a bounded SNPE-style conditional posterior training loop for mechanism-faithful SBI recovery.
---

# SBI SNPE Training Loop

Use this skill to train or emulate a small conditional neural posterior estimator from simulated `(theta, x)` pairs and query it at an observation.

Do not use it for SNLE/SNRE objectives or for posterior validation alone.

## Inputs
- Simulated `theta` and `x` pairs.
- Prior bounds or prior metadata.
- Observation `x_o`.
- Bounded training hyperparameters and seed.

## Outputs
- Posterior samples for `x_o`.
- Training diagnostics and mechanism checks.
- Declaration of full-package or reduced/proxy execution.

## Workflow
1. Validate that `theta` and `x` are aligned and finite.
2. Fit a conditional posterior estimator that depends on `x`.
3. Sample from the estimated posterior conditioned on `x_o`.
4. Record loss/proxy diagnostics and sample summaries.
5. Mark reduced implementations as proxy recovery.

## Validation
Run:

```bash
python scripts/snpe_proxy.py --num-simulations 256 --observation 1.25
python tests/test_snpe_proxy.py
```

## Limitations
- The included script is a reduced Gaussian SNPE-style proxy for fast recovery, not the full `sbi` package.
- It must be declared as proxy recovery in soft mode.
