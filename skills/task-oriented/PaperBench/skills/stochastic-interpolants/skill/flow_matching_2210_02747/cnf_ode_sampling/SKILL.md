---
name: cnf_ode_sampling
description: Integrate learned Flow Matching vector fields with fixed-step ODE solvers and report trajectory/error diagnostics.
---

# CNF ODE Sampling

Use this skill when a recovery or implementation has a time-dependent vector field and needs to generate samples by integrating the CNF ODE from noise toward data. Do not use it to define conditional OT paths or train the CFM loss.

## Inputs

- Initial vector `x0`.
- A vector-field callable `f(t, x)` or one of the built-in deterministic proxy fields.
- Step count and solver name: `euler`, `midpoint`, or `rk4`.

## Outputs

- Final state.
- Full trajectory including the initial state.
- Number of function evaluations.
- Optional mean-squared error against an analytic reference.

## Workflow

1. Validate the step count and solver choice.
2. Integrate over `t in [0, 1]` using the chosen fixed-step solver.
3. Record NFE so recovery can compare low-cost samplers.
4. Compare against an analytic displacement reference when available.

## Validation

Run:

```bash
python tests/test_ode_sampling.py
python scripts/ode_sampling.py --x0 '[0, 1]' --velocity '[2, -1]' --steps 4 --solver rk4
```

## Limitations

This skill provides bounded deterministic ODE checks for recovery. It is not an adaptive ODE package and does not estimate likelihoods.

Cycle refinement: recovery reports NFE because Flow Matching sampling cost is part of the mechanism check.
