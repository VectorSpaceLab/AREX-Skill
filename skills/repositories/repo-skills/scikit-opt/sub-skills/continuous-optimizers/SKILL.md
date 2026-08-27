---
name: continuous-optimizers
description: "Select and run DE, PSO, SA schedules, and AFSA for continuous optimization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Continuous optimizers

Use this sub-skill for non-GA continuous minimization with DE, PSO, simulated annealing, and AFSA.

Read:
- [`references/api-reference.md`](references/api-reference.md) when you need constructor signatures, supported constraints, aliases, or result fields.
- [`references/workflows.md`](references/workflows.md) when you are choosing an optimizer or preparing a tiny run.
- [`references/troubleshooting.md`](references/troubleshooting.md) when runs fail, constraints are rejected, or the objective shape is wrong.
- [`scripts/smoke_continuous_optimizers.py`](scripts/smoke_continuous_optimizers.py) to verify a local installation with a deterministic sphere-style smoke.

Use this sub-skill when:
- the objective is continuous and scalar-valued;
- the problem is handled by DE, PSO, SA/SAFast/SABoltzmann/SACauchy, or AFSA;
- you need `best_x`/`best_y` validation or PSO history capture.

Route elsewhere:
- GA-family or custom operators -> `genetic-algorithms`
- route/permutation/TSP problems -> `routing-and-combinatorial`
- objective-vectorization, caching, run modes, or benchmark helpers -> `objective-functions-and-speedups`

Important limits:
- PSO enforces `constraint_ueq` only; `constraint_eq` is not implemented.
- SA and AFSA do not accept constraint callbacks; use penalties or projection in the objective if you need feasibility control.
