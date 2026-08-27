# Optimization workflows

This reference covers the solve/build/modify flow for PyPSA optimization tasks.
It assumes the network already exists and the caller wants to solve, inspect, or
customize the model.

## Core accessor signatures

```python
n.optimize(
    snapshots=None,
    multi_investment_periods=False,
    transmission_losses=False,
    linearized_unit_commitment=False,
    model_kwargs=None,
    extra_functionality=None,
    assign_all_duals=False,
    solver_name=None,
    solver_options=None,
    log_to_console=None,
    compute_infeasibilities=False,
    include_objective_constant=None,
    committable_big_m=None,
    meshed_thresholds=None,
    piecewise_options=None,
    **kwargs,
)

n.optimize.create_model(
    snapshots=None,
    multi_investment_periods=False,
    transmission_losses=False,
    linearized_unit_commitment=False,
    consistency_check=True,
    include_objective_constant=None,
    committable_big_m=None,
    meshed_thresholds=None,
    piecewise_options=None,
    **kwargs,
)

n.optimize.solve_model(
    extra_functionality=None,
    solver_name=None,
    solver_options=None,
    log_to_console=None,
    assign_all_duals=False,
    **kwargs,
)
```

## Default solve path

Use `n.optimize()` when the data already defines the desired model class.
PyPSA builds a Linopy model, solves it, and writes the solution back to the
network in one step.

Recommended baseline for a tiny smoke or a first solve:

```python
n.consistency_check(strict=["unknown_buses", "unknown_carriers"])
status, condition = n.optimize(
    solver_name="highs",
    log_to_console=False,
    include_objective_constant=False,
)
```

Notes:
- `solver_name="highs"` is the safe default open-source path.
- `log_to_console=False` keeps smoke runs quiet when the solver supports it.
- `include_objective_constant=False` is numerically cleaner for LPs.
- `include_objective_constant=None` currently raises a FutureWarning and falls
  back to the historical default; set it explicitly to avoid drift.
- `n.objective` stores the optimized objective, while `n.objective_constant`
  stores the capital cost of already-built capacity when it is included.

## Create, modify, solve

Use `create_model()` when you need to add constraints, change the objective, or
inspect the raw Linopy model before solving.

```python
m = n.optimize.create_model(include_objective_constant=False)
m.add_constraints(m.variables["Generator-p"].sum() <= 1e6, name="custom_total_dispatch_cap")
status, condition = n.optimize.solve_model(
    solver_name="highs",
    log_to_console=False,
)
```

Guidance:
- `extra_functionality(n, snapshots)` is the callback form of the same pattern.
  PyPSA calls it after the model is built and before the solve step.
- Use `n.model` while the model is alive in memory; custom constraints and
  custom variables are not exported with the network file formats.
- If you need duals for known constraints, pass `assign_all_duals=True`.
  Custom constraints remain available on `n.model.dual`; only named
  `GlobalConstraint-*` additions can be copied into the network tables.

## Capacity expansion, dispatch, and storage

The default objective co-optimizes:
- dispatch for generators, links, processes, storage units, and stores
- capacity expansion for extendable nominal capacities
- storage state and cyclicity constraints

Key modeling switches:
- `p_nom_extendable`, `s_nom_extendable`, `e_nom_extendable` enable investment.
- `Store` and `StorageUnit` are different storage formulations; both can be
  optimized and both support extendable capacities.
- `fix_optimal_capacities()` freezes optimized capacity for a follow-up
  operational solve.
- `fix_optimal_dispatch()` copies optimized dispatch into `p_set` and is a
  handy pre-step before a power-flow run.
- `add_load_shedding()` injects a high-cost rescue generator at selected buses
  and is useful for infeasibility triage.

Common symptoms:
- Extendable assets without capital cost usually do nothing useful.
- Existing capacity on extendable assets is only reflected in the objective when
  the objective constant is included.
- Storage initial energy and cyclicity need to be set deliberately when the
  horizon spans multiple investment periods.

## Unit commitment and dispatch limits

`committable=True` introduces commitment variables and turns the model into a
MILP. Typical companions are `p_min_pu`, `p_max_pu`, `start_up_cost`,
`shut_down_cost`, `min_up_time`, `min_down_time`, and ramp limits.

Important controls:
- `linearized_unit_commitment=True` relaxes commitment binaries to the unit
  interval and adds tightening constraints.
- `committable_big_m` overrides the inferred big-M bound for committable and
  extendable assets.
- `linearized_unit_commitment=True` is not compatible with modular committables.
- `transmission_losses` activates piecewise linear loss approximations for lines
  and transformers.

### `transmission_losses`

Accepted forms:
- `False`: disabled
- `True`: secant-based approximation with default tolerances
- `{"mode": "secants", ...}`: secant-based with explicit tolerances
- `{"mode": "tangents", "segments": N}`: tangent-based approximation
- legacy integer input is deprecated and should be replaced by the explicit
  dict form

Practical notes:
- Secant mode needs finite `s_nom_max` values.
- Tangent mode can underestimate losses and depends on the chosen segment count.
- `n.lines_t.p0 + n.lines_t.p1` gives the realized line loss after a solve.

## Global and custom constraints

PyPSA supports built-in global constraint types and ad hoc Linopy constraints.
Use built-ins when the constraint is semantically standard; use Linopy directly
when it is bespoke.

Built-in global constraint families include:
- primary energy / emissions
- operational limits
- transmission expansion cost and volume limits
- technology capacity expansion limits
- carrier growth limits

Helpful patterns:
- Add a `GlobalConstraint` component before the solve to express a standard
  system-wide limit.
- Use `assign_all_duals=True` if you want the duals of recognized constraints
  copied back into the network.
- If you add a custom constraint after `create_model()`, keep the original
  `n.model` object around; that is where the resulting expression and dual live.

Minimal custom-constraint pattern:

```python
m = n.optimize.create_model()
m.add_constraints(m.variables["Generator-p"].sum() <= 1e6, name="custom_total_dispatch_cap")
n.optimize.solve_model(solver_name="highs", log_to_console=False)
```

## Multi-investment / pathway planning

Use `multi_investment_periods=True` when snapshots are a `pd.MultiIndex` with a
`period` level and the network should optimize across several investment years.

Requirements and reminders:
- call `n.set_investment_periods(...)` first
- build_year and lifetime determine whether an asset is active in a given period
- `state_of_charge_initial` / `e_initial` and cyclicity can be set per period when needed
- carrier growth limits and technology expansion limits become especially useful
  in long-horizon planning

Typical solve form:

```python
n.optimize(multi_investment_periods=True, solver_name="highs", log_to_console=False)
```

## Stochastic optimization and risk preference

Stochastic optimization requires scenarios to be defined before the solve.
Scenario data is broadcast across the network and all scenario weights must sum
to 1.

Workflow:
1. Add all components.
2. Call `n.set_scenarios({...})`.
3. Update scenario-specific time series or parameters.
4. Solve with `n.optimize()` or with `multi_investment_periods=True`.
5. Optionally set CVaR risk preference with `n.set_risk_preference(alpha, omega)`.

Constraints and caveats:
- scenarios cannot be changed once set
- piecewise attribute data and scenarios are not currently combined
- `set_risk_preference()` requires scenarios
- CVaR is not available with quadratic marginal costs
- `alpha` must lie in `(0, 1)` and `omega` in `[0, 1]`

A risk-neutral stochastic solve still uses scenario weights on the objective.
A risk-averse solve adds CVaR auxiliary variables and constraints.

## MGA and rolling horizon

Use MGA when you already have a solved network and want nearby alternatives.
Use rolling horizon when you want to solve a long time series in chunks.

MGA helpers:
- `optimize_mga()` for a single alternative objective under a cost slack
- `optimize_mga_in_direction()` for low-dimensional trade-off exploration
- `optimize_mga_in_multiple_directions()` for parallel exploration of several directions

Rolling horizon helper:
- `optimize_with_rolling_horizon(horizon=..., overlap=...)`
- `overlap` must be smaller than `horizon`
- store and storage-unit states are carried forward between windows

Use `snapshots=` to restrict either workflow to a subset of the horizon.

## Piecewise curves

`piecewise_options` is a list of dicts or `PiecewiseOptions` objects that
override the default piecewise formulation for selected component/attribute pairs.
Each entry may specify:
- `component`
- `attribute`
- `sign`
- `name`
- `method`
- `cumulative_attr`

Interpretation notes:
- `sign` chooses whether the model enforces `y == f(x)`, `y <= f(x)`, or
  `y >= f(x)`.
- `cumulative_attr=True` means the y-axis represents an integral of marginal
  values.
- `cumulative_attr=False` means the y-axis is read directly at the operating
  point.
- For per-unit x-axis piecewise curves on extendable components, fixed nominal
  capacity is required so the x-axis can be scaled to absolute values.

Useful patterns:
- piecewise marginal costs for generators, links, processes, storage units, and
  stores
- piecewise capital costs for extendable assets
- piecewise efficiency or rate curves where the y-value is read directly

If you are unsure whether a piecewise failure is a data-shape bug or a model
issue, reduce to a single component and a single breakpoint pair first.
