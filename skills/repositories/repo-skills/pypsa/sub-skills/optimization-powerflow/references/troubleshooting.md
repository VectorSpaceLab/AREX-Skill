# Troubleshooting

This reference is the fast triage map for optimization and power-flow failures.
Start with the smallest possible network that still reproduces the problem.

## First checks

1. Run `n.consistency_check()` before solving.
2. Make sure every referenced bus and carrier exists.
3. Confirm that time-series tables use the snapshot index you expect.
4. Set the solver explicitly, usually `solver_name="highs"`.
5. For power flow, seed with `n.lpf()` before retrying `n.pf(use_seed=True)`.

## Symptom-to-fix map

| Symptom | Likely cause | Safe next step |
|---|---|---|
| `n.optimize()` returns infeasible or stalls | Missing supply, conflicting limits, bad topology, or solver difficulty | Run `n.consistency_check(strict=["unknown_buses", "unknown_carriers", "time_series", "shapes"])`, add load shedding, and shrink to a smaller network or shorter time window. |
| Infeasible solve and Gurobi is available | Need an IIS trace | Re-run with `solver_name="gurobi"` and `compute_infeasibilities=True`, then inspect the reported conflicting constraints. |
| Infeasible solve and Gurobi is not available | No IIS support in the current backend | Add load shedding with `n.optimize.add_load_shedding()`, reduce the model, and inspect the model constraints directly. |
| Solver backend not found | `solver_name` does not match an installed backend | Fall back to `solver_name="highs"` or install the requested solver before debugging the model. |
| Large MILP is too slow or numerically unstable | Open-source solver limits or scaling issues | Reduce spatial/temporal resolution, simplify the model, or try a commercial solver if one is already licensed. |
| `n.pf()` does not converge | Zero impedances, poor seed, unit mismatch, or large phase shifts | Verify line and transformer impedances, check MW/kW and radians/degrees, run `n.lpf()`, and retry with `use_seed=True`. |
| Slack absorbs too much mismatch in PF | Single-slack formulation is too brittle for the network | Retry with `distribute_slack=True` and choose `slack_weights="p_set"`, `"p_nom"`, or `"p_nom_opt"`. |
| `linearized_unit_commitment=True` raises a `ValueError` | Modular committables are not compatible with the relaxed UC formulation | Remove modularity or use the standard committable formulation instead. |
| Capacity / ramp limits look too tight | Inferred big-M is too small for the network | Override with `committable_big_m` and rerun the solve. |
| `transmission_losses` or piecewise setup fails | Invalid mode, missing breakpoint data, or per-unit curves on extendable assets | Use `transmission_losses=True` or the explicit dict form, ensure finite `s_nom_max`, and simplify to one component / one curve first. |
| Scenario solve or CVaR setup fails | Scenario weights, unsupported data combination, or quadratic operational costs | Make sure scenarios sum to 1, set risk preference only after scenarios, and remove quadratic marginal costs when using CVaR. |
| `include_objective_constant` warns on solve | The value was not passed explicitly | Set `include_objective_constant=False` for the smoke path, or `True` if you deliberately want the constant included. |
| Undefined buses or carriers appear in validation | The network was assembled without the required `Carrier` rows or bus names | Add the missing `Carrier` rows, check bus names, then rerun `n.consistency_check()`. |

## Practical repair sequence for infeasible optimization

When HiGHS reports infeasibility and Gurobi is not available, use this order:

```python
n.consistency_check(strict=["unknown_buses", "unknown_carriers", "time_series", "shapes"])
n.optimize.add_load_shedding(marginal_cost=1e6, p_nom=1e9)
status, condition = n.optimize(solver_name="highs", log_to_console=False, include_objective_constant=False)
```

If the reduced model is still infeasible, remove half the buses or snapshots,
repeat the consistency check, and compare the resulting model against the full
case.

## Practical repair sequence for PF convergence

```python
n.optimize.fix_optimal_dispatch()
n.lpf()
result = n.pf(use_seed=True, distribute_slack=True, slack_weights="p_nom_opt")
```

If that still fails:
- verify that all branch impedances are non-zero
- check that the load and generation units are in the correct power units
- inspect whether the angle spread is extreme for the current topology
- simplify the line model or remove the most problematic transformer phase shift

## Notes on optional backends

- Commercial solver features such as IIS tracing are optional, not required for
  a healthy PyPSA installation.
- If an optional solver or package is missing, do not treat that as a model bug
  until the same workflow has been tried with HiGHS or on a smaller network.
- The absence of a solver backend is usually a deployment issue; infeasibility is
  usually a model or data issue.
