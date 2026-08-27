# API reference

All optimizers in this sub-skill minimize a single scalar objective. DE and PSO evaluate ordinary one-candidate functions internally; SA and AFSA call the objective directly on one candidate vector.

## Differential Evolution (DE)

Signature:

```python
DE(func, n_dim, F=0.5, size_pop=50, max_iter=200, prob_mut=0.3,
   lb=-1, ub=1, constraint_eq=(), constraint_ueq=(), n_processes=0)
```

Use DE when you need bounds plus equality and/or inequality constraints.

Key parameters:

- `F`: mutation scale in `X[r1] + F * (X[r2] - X[r3])`.
- `prob_mut`: crossover mask rate.
- `lb` / `ub`: scalar or length-`n_dim` sequences.
- `constraint_eq`, `constraint_ueq`: both are penalized in the objective.
- `n_processes`: forwarded to the shared objective wrapper; it matters only if the objective has been prepared for a parallel mode.

Returns and attributes:

- `run()` returns `(best_x, best_y)`.
- `generation_best_X`, `generation_best_Y`, `all_history_Y`.
- `best_x`, `best_y`.

Validation:

- `best_x` should flatten to length `n_dim`.
- `best_y` should be finite.
- Re-evaluating the objective at `best_x` should stay finite.

## Particle Swarm Optimization (PSO)

Signature:

```python
PSO(func, n_dim=None, pop=40, max_iter=150, lb=-100000.0, ub=100000.0,
    w=0.8, c1=0.5, c2=0.5, constraint_eq=(), constraint_ueq=(),
    verbose=False, dim=None, n_processes=0)
```

Use PSO when you want swarm search with inertia and cognitive/social weights.

Key parameters:

- `n_dim` and `dim` are aliases; pass either one.
- `w`, `c1`, `c2`: inertia, cognitive, and social weights.
- `constraint_ueq`: inequality constraints only. `constraint_eq` is not implemented.
- `record_mode`: set after construction to store `X`, `V`, and `Y` snapshots.
- `n_processes`: forwarded to the shared objective wrapper; it matters only if the objective has been prepared for a parallel mode.
- `precision` and `N` on `run(max_iter=None, precision=None, N=20)`: stop when the swarm's personal-best spread stays below `precision` for `N` consecutive iterations.

Returns and attributes:

- `run()` returns `(best_x, best_y)`.
- `gbest_x`, `gbest_y`, `gbest_y_hist`.
- `best_x`, `best_y` compatibility aliases.
- `record_value` with keys `X`, `V`, `Y` when `record_mode=True`.

Validation:

- `record_value` arrays should all have the same length.
- `gbest_x` usually comes back as shape `(1, n_dim)`; flatten before comparison.
- `gbest_y` may be array-like; coerce it to a scalar before checks.

## Simulated Annealing (SA)

`SA` is the default alias for `SAFast`.

Shared signatures:

```python
SAFast(func, x0, T_max=100, T_min=1e-7, L=300, max_stay_counter=150, **kwargs)
SABoltzmann(func, x0, T_max=100, T_min=1e-7, L=300, max_stay_counter=150, **kwargs)
SACauchy(func, x0, T_max=100, T_min=1e-7, L=300, max_stay_counter=150, **kwargs)
```

Use SA when you want a single starting point and a temperature schedule.

Key parameters:

- `x0`: initial 1-D point.
- `T_max`, `T_min`: starting and ending temperatures; the constructor asserts `T_max > T_min > 0`.
- `L`: inner-chain length at each temperature.
- `max_stay_counter`: stop after repeated non-improvement.
- Bounds are optional but must be given as `lb` and `ub` together.
- `hop`: step scale when using bounded SA.
- `SAFast`: uses `m`, `n`, and `quench` for its cooling schedule.
- `SABoltzmann` and `SACauchy`: use `learn_rate`.
- Do not confuse SAFast's `quench` with AFSA's `q`.

Returns and attributes:

- `best_x`, `best_y`.
- `generation_best_X`, `generation_best_Y`.
- `best_x_history`, `best_y_history` compatibility aliases.

Validation:

- `best_x` should match the length of `x0`.
- `best_y` should be finite.
- With bounds, every candidate should stay inside the box after clipping.

## Artificial Fish Swarm Algorithm (AFSA)

Signature:

```python
AFSA(func, n_dim, size_pop=50, max_iter=300, max_try_num=100,
     step=0.5, visual=0.3, q=0.98, delta=0.5)
```

Use AFSA when you want fish-swarm style search with prey, swarm, and follow behavior.

Key parameters:

- `size_pop`: fish count.
- `max_iter`: outer loop count.
- `max_try_num`: number of prey attempts before a random move.
- `step`: movement scale.
- `visual`: neighborhood radius.
- `q`: visual decay per iteration.
- `delta`: crowding threshold.

Returns and attributes:

- `best_x`, `best_y`.
- Deprecated compatibility aliases `best_X`, `best_Y`.

Validation:

- `best_x` should flatten to length `n_dim`.
- `best_y` should be finite.
- Smaller `step` and larger `visual` often help on tiny smoke runs.

## Result checks

- Re-evaluate the objective at the returned candidate.
- Confirm `np.isfinite(np.asarray(best_y)).all()`.
- For PSO record mode, confirm `len(record_value["X"]) == len(record_value["V"]) == len(record_value["Y"])`.
