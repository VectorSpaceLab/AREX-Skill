---
name: sbi_simulator_prior_protocol
description: Prepare simulator, prior, observation, and simulated pair contracts for simulation-based inference workflows.
---

# SBI Simulator Prior Protocol

Use this skill when a recovery or implementation task needs to turn a prior and black-box simulator into auditable `(theta, x)` simulation pairs for neural SBI.

Do not use it to evaluate analytic likelihoods or to train the posterior estimator itself.

## Inputs
- Prior sampler or bounds plus random seed.
- Simulator callable or simulator specification.
- Number of simulations.
- Optional observation `x_o`.

## Outputs
- Two-dimensional `theta` and `x` arrays with matching row counts.
- Shape metadata and provenance.
- Failure count and finite-value status.

## Workflow
1. Normalize scalar parameter and observation values to row-major two-dimensional arrays.
2. Sample parameters from the prior with a deterministic seed.
3. Run the simulator without requiring likelihood evaluation.
4. Check row alignment, finite values, and failure counts.
5. Return provenance for downstream training and recovery logs.

## Validation
Run:

```bash
python scripts/sim_protocol.py --smoke
python tests/test_sim_protocol.py
```

## Limitations
- This skill defines the data protocol only; it does not choose SNPE/SNLE/SNRE.
- Failed simulations must be reported, not silently hidden.
