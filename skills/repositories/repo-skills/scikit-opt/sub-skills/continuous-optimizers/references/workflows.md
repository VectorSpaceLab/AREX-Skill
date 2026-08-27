# Workflows

## 1. Choose a family

| Problem shape | First choice | Why |
| --- | --- | --- |
| Bounded continuous problem with equality and inequality constraints | DE | Current API supports both constraint types through penalties. |
| Bounded continuous problem with inequality constraints only | PSO | Swarm control, optional record mode, and precision stop. |
| Single start point, schedule comparison, or box-aware local search | SA | SA/SAFast/SABoltzmann/SACauchy share one simple interface. |
| Simple swarm search without built-in box constraints | AFSA | Compact parameter set and cheap smoke runs. |

If equality constraints matter, avoid PSO. If you need hard feasibility and the objective is awkward to penalize, DE is the safer default.

## 2. Run a tiny smoke

Use a deterministic sphere-style objective and a small population:

```python
import numpy as np

def sphere(x):
    x = np.asarray(x, dtype=float).reshape(-1)
    return float(np.dot(x, x))
```

Then:

1. Set `numpy.random.seed(...)` before constructing the optimizer.
2. Use 2-3 dimensions and a tiny box such as `[-1, 1]`.
3. Keep `size_pop` around 8-12 and `max_iter` around 4-8.
4. Run the optimizer.
5. Flatten `best_x`, recompute `sphere(best_x)`, and check that all values are finite.

For PSO, turn on `record_mode` only for tiny runs.

## 3. Constraint strategy

- **DE**: pass `constraint_eq` and `constraint_ueq` directly.
- **PSO**: pass only `constraint_ueq`; equality constraints are not implemented.
- **SA / AFSA**: encode constraints inside the objective, either with a finite penalty or with projection/clipping before scoring.

## 4. Algorithm-specific tuning

- **DE**: start with `F` around `0.3-0.8` and `prob_mut` around `0.1-0.5` for smoke-sized runs.
- **PSO**: tune `w`, `c1`, and `c2`; use `precision` only when the objective is stable enough for a spread-based stop test.
- **SA**: use `SA` for the default fast schedule, `SABoltzmann` for gentler Gaussian steps, and `SACauchy` for heavier-tailed moves. Keep `T_max > T_min > 0`.
- **AFSA**: keep `step` modest, `visual` large enough to find neighbors, and `max_try_num` high enough that prey can succeed before random motion.

## 5. Validation habit

After every run, check:

- the returned candidate is finite;
- the returned objective value is finite;
- PSO history arrays are aligned when `record_mode=True`;
- any constraint residuals are finite and sensible.
