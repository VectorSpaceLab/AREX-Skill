# Power-flow workflows

This reference covers the linear and non-linear power-flow paths and the
handoff from an optimization result to a voltage solve.

## Core accessor signatures

```python
n.lpf(snapshots=None, skip_pre=False)

n.pf(
    snapshots=None,
    skip_pre=False,
    x_tol=1e-06,
    use_seed=False,
    distribute_slack=False,
    slack_weights="p_set",
)

n.optimize.optimize_and_run_non_linear_powerflow(
    snapshots=None,
    skip_pre=False,
    x_tol=1e-06,
    use_seed=False,
    distribute_slack=False,
    slack_weights="p_set",
    **kwargs,
)
```

## Linear power flow (`n.lpf()`)

Use `n.lpf()` when you want a fast linearized flow result, a seed for the
non-linear solve, or a quick check that the network topology and setpoints are
reasonable.

Inputs that matter most:
- bus voltage bases (`v_nom`)
- branch impedances (`x`, and `r` for DC-style linearized checks)
- generator / load setpoints
- a connected topology with valid bus assignments

Outputs written back to the network include:
- `buses_t.v_ang`
- `buses_t.v_mag_pu`
- `lines_t.p0` / `lines_t.p1`
- `transformers_t.p0` / `transformers_t.p1`
- `links_t.p0` / `links_t.p1`
- one-port injections such as `generators_t.p`

Useful pattern:

```python
n.optimize.fix_optimal_dispatch()
n.lpf()
```

`fix_optimal_dispatch()` is optional, but it is a convenient way to copy the
latest optimized dispatch into `p_set` before the flow solve.

## Non-linear power flow (`n.pf()`)

Use `n.pf()` when you need voltage magnitudes and angles from the Newton-Raphson
solve.

Parameters worth remembering:
- `x_tol` controls the residual tolerance.
- `use_seed=True` uses the current voltage guesses instead of the flat start.
- `distribute_slack=True` distributes active-power slack across generators.
- `slack_weights` can be `"p_set"`, `"p_nom"`, `"p_nom_opt"`, a
  generator/bus `Series`, or a per-subnetwork dictionary.

Slack and seed behavior:
- If no slack generator is present, the first generator in the subnetwork is
  used as the slack generator.
- If multiple slack generators are marked, only one is retained as the true
  slack and the rest are demoted to PV.
- `use_seed=True` is especially helpful when transformer phase shifts or a
  large angle spread make the flat start too far from the solution.
- `distribute_slack=True` is useful when a single slack bus would otherwise
  absorb all mismatch.

Typical workflow:

```python
n.optimize.fix_optimal_dispatch()
n.lpf()
result = n.pf(use_seed=True, distribute_slack=True, slack_weights="p_nom_opt")
```

## Optimize then run non-linear PF

Use `n.optimize.optimize_and_run_non_linear_powerflow()` when you want the full
solve in one call: optimization first, then a non-linear power-flow pass on the
optimized dispatch.

This helper is convenient when:
- you want to validate an optimized network with voltage results immediately
- you need a compact smoke or notebook path
- you want a single API call for "optimize, then run PF on all snapshots"

Typical call:

```python
out = n.optimize.optimize_and_run_non_linear_powerflow(
    solver_name="highs",
    log_to_console=False,
    include_objective_constant=False,
    use_seed=True,
    distribute_slack=True,
    slack_weights="p_nom_opt",
)
```

The returned dictionary includes the optimization status and the PF convergence
summary.

## Data and convergence checks

If PF fails, check the following first:
- lines and transformers must not be singular; `r + jx` should not be zero
- bus voltage bases and branch units should be consistent
- large angle differences may indicate that the model is too far from the flat
  start
- phase-shifting transformers can benefit from `use_seed=True`

A good repair sequence is:
1. run `n.lpf()`
2. rerun `n.pf(use_seed=True)`
3. enable `distribute_slack=True` if the slack bus is overburdened
4. simplify the topology or reduce the time window if the model is still unstable

If you already have optimized dispatch and only need PF, copying the optimized
solution into `p_set` before the PF solve keeps the two stages aligned.
