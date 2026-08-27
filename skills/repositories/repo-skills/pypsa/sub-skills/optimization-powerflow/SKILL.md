---
name: optimization-powerflow
description: "Route PyPSA solve, solver, custom constraint, stochastic,
  multi-investment, MGA, rolling-horizon, piecewise, loss, and power-flow
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# optimization-powerflow

Use this sub-skill for PyPSA tasks that need to:
- solve or re-solve a network with `n.optimize()`, `n.optimize.create_model()`, `n.optimize.solve_model()`, or `extra_functionality`
- choose a solver, pass `solver_options`, or diagnose solver availability and infeasibility
- work with capacity expansion, dispatch, storage, unit commitment, global/custom constraints, `multi_investment_periods`, stochastic scenarios, MGA, rolling horizon, piecewise curves, or transmission losses
- run `n.lpf()`, `n.pf()`, or `n.optimize.optimize_and_run_non_linear_powerflow()`
- debug convergence, slack seeding, big-M, modular committables, or missing optional solver backends

Do not use this sub-skill for:
- building or validating network structure from scratch — use `network-modeling`
- importing or exporting data — use `network-io-data`
- statistics, maps, or result plots — use `analysis-visualization`

## Start here
- [references/optimization-workflows.md](references/optimization-workflows.md) — solve, model-edit, custom-constraint, stochastic, multi-investment, MGA, rolling-horizon, piecewise, and loss workflows.
- [references/power-flow-workflows.md](references/power-flow-workflows.md) — linear and non-linear power-flow workflows, seeding, distributed slack, and optimize-then-PF handoff.
- [references/solver-reference.md](references/solver-reference.md) — solver defaults, solver flags, and license-aware notes.
- [references/troubleshooting.md](references/troubleshooting.md) — quick diagnosis map for infeasibility, convergence, data, and backend failures.

## Smoke helpers
- [scripts/pypsa_optimize_smoke.py](scripts/pypsa_optimize_smoke.py) — tiny HiGHS solve plus a second create-model/solve-model pass with a custom constraint.
- [scripts/pypsa_powerflow_smoke.py](scripts/pypsa_powerflow_smoke.py) — tiny `lpf`/`pf` smoke with seeded distributed slack and an optional combined optimize-then-PF run.
