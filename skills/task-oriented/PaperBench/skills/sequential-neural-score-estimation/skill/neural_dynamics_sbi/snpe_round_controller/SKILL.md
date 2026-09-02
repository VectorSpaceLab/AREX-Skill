---
name: snpe_round_controller
description: Coordinate prior and posterior-guided simulation rounds for a bounded SNPE-style recovery experiment.
---

# Sequential SNPE Round Controller

Use this skill when an experiment needs auditable SNPE-style rounds: initial prior simulations, estimator fitting, and optional posterior-guided proposal narrowing. Do not use it to claim full neural density-estimator training unless that runtime actually ran.

## Inputs
- Prior bounds for each parameter.
- Observed summary.
- Callable simulator/summary function.
- Round count, simulations per round, and seed.

## Outputs
- Round logs with proposal centers/scales and simulation counts.
- Accumulated summaries and parameters.
- Final posterior estimate and mechanism flags.

## Workflow
1. Sample the first round from the prior.
2. Fit the posterior estimator on all accumulated simulated pairs.
3. If more rounds are requested, sample around the posterior mean with clipped, reduced proposal scale.
4. Record proposal narrowing and all simulation counts.

## Validation
Run `python tests/test_round_controller.py` from this skill directory.

## Limitations
This controller is a deterministic reduced mechanism check. It intentionally uses a lightweight posterior surrogate for bounded recovery.
