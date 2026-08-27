# Solver reference

PyPSA delegates optimization to Linopy and then to an external solver. For this
sub-skill, the safest baseline is the open-source HiGHS solver.

## Recommended defaults

| Parameter | Recommended | Notes |
|---|---|---|
| `solver_name` | `"highs"` | Default open-source path; good for tiny smoke runs and most examples. |
| `solver_options` | `{}` or solver-specific flags | Passed through to Linopy and then to the solver backend. |
| `log_to_console` | `False` | Suppresses solver chatter when the backend supports it. |
| `include_objective_constant` | `False` | Better LP conditioning; set explicitly to avoid the future-warning path. |
| `compute_infeasibilities` | `False` | Set `True` only when a Gurobi-backed IIS diagnosis is available. |

## What the knobs do

- `solver_name` selects the backend.
- `solver_options` forwards backend-specific parameters such as tolerances,
  barrier settings, crossover controls, or random seeds.
- `log_to_console` is a solver output switch. Some solvers honor it, others
  ignore it.
- `include_objective_constant=False` removes already-built CAPEX from the model
  objective and usually improves numerical conditioning.
- `compute_infeasibilities=True` asks PyPSA to print an irreducible inconsistent
  subsystem if the backend supports it.

## Solver choice guidance

| Solver | Typical role | Caveat |
|---|---|---|
| HiGHS | Default free LP/MILP solver | Best first choice for small and medium tests; may struggle on very large MILPs. |
| Gurobi | Fast commercial LP/MILP/QP solver | Needed for IIS-based infeasibility tracing; requires a valid license. |
| CPLEX | Commercial alternative | Often strong on large models; option names differ from HiGHS and Gurobi. |
| Xpress | Commercial alternative | Similar caveat: solver-specific flags differ. |
| SCIP / CBC / GLPK | Open-source alternatives | Useful when installed, but not a substitute for a failed model formulation. |

## Example option bundles

A few representative flag patterns:

```python
# HiGHS: interior point with crossover disabled
n.optimize(solver_name="highs", solver="ipm", run_crossover="off", random_seed=123)

# Gurobi: barrier-like path with crossover disabled
n.optimize(solver_name="gurobi", method=2, crossover=0, Seed=123)

# SCIP: choose the barrier-style LP algorithm
n.optimize(solver_name="scip", solver_options={"lp/initalgorithm": "b"})
```

## When a solver is missing

If the requested backend is not installed or not visible to Linopy:
1. switch to `solver_name="highs"`
2. remove backend-specific flags that the solver does not support
3. confirm the solver is available before assuming the model itself is wrong

If the model is infeasible, solver selection alone will not fix it. In that case,
move to the troubleshooting checklist: consistency checks, load shedding,
model reduction, and, when available, IIS analysis.
