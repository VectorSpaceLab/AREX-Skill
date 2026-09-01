---
name: stochastic_vi_chain
description: Run bounded constant-step noisy stochastic optimization chains that model stochastic VI iterates as a Markov process around an optimum.
---

# Stochastic VI Chain

Use this skill when a recovery or implementation needs deterministic evidence for the paper's view of stochastic VI optimization as a Markov chain. Do not use it to claim full probabilistic-programming VI training unless the gradient oracle is connected to a real model.

## Inputs

- `chains`: positive number of independent optimization runs.
- `iterations`: positive number of stochastic update steps.
- `dimensions`: positive variational parameter dimension.
- `learning_rate`, `noise_scale`, `seed`, and optional optimum vector.

## Outputs

- JSON containing `iterates`, `gradients`, `initial_parameters`, `optimum`, and run metadata.
- Chain-major arrays: `chains x iterations x dimensions`.

## Workflow

1. Choose or supply a known optimum.
2. Initialize chains away from the optimum with deterministic seed control.
3. At each step, evaluate a negative-quadratic gradient plus zero-mean Gaussian noise.
4. Apply a constant-step stochastic gradient update and record the trace.
5. Use the trace for downstream Rhat, ESS, MCSE, and iterate-averaging checks.

## Validation

Run:

```bash
python3 scripts/simulate_chains.py --chains 4 --iterations 120 --dimensions 5 --output /tmp/stochastic_vi_chains.json
python3 tests/test_simulate_chains.py
```

## Limitations

The bundled simulator is a reduced proxy for optimizer dynamics. It preserves stochastic iterate behavior and trainable-parameter updates but does not replace a full model-specific ELBO gradient.
