# Workflows: sliced approximations and reproducible validation

Use these workflows when a task asks to replace dense OT with a faster approximation, or when sliced estimates need to be reproducible and validated. For exact EMD/Sinkhorn mechanics, route to `core-solvers`; for backend installation, route to `backend-and-batch`.

## 1. Replace exact OT with sliced Wasserstein distance

Use this when the user needs a scalar discrepancy between sample clouds and does not need a full dense transport plan.

```python
import numpy as np
import ot

rng = np.random.RandomState(0)
X_s = rng.normal(size=(128, 8))
X_t = rng.normal(loc=0.25, size=(128, 8))
a = ot.unif(X_s.shape[0])
b = ot.unif(X_t.shape[0])

swd, log = ot.sliced.sliced_wasserstein_distance(
    X_s, X_t, a=a, b=b, n_projections=128, p=2, seed=0, log=True
)
print(float(swd), log["projections"].shape, len(log["projected_emds"]))
```

Validation steps before scaling up:

1. Assert `X_s.shape[1] == X_t.shape[1]` and weights are nonnegative and sum to one.
2. Fix `seed` or pass a saved `projections` matrix for reproducibility.
3. Repeat a few seeds or projection matrices and report mean/std if the result drives a decision.
4. On a tiny representative subset, compare the trend against a dense baseline from `core-solvers` rather than expecting equality.
5. Record `n_projections`, `p`, any `scaler`, and the seed/projection source with the result.

Run the bundled smoke check from this sub-skill directory when adapting the workflow:

```bash
python scripts/sliced_gaussian_smoke.py --mode sliced --seed 0
```

## 2. Stabilize sliced Wasserstein when feature scales differ

Random projections can be dominated by high-magnitude features. Fit a scaler once on representative data and reuse it across calls.

```python
import numpy as np
import ot

rng = np.random.RandomState(1)
X_s = np.column_stack([rng.normal(1000, 100, 200), rng.normal(0, 1, 200)])
X_t = np.column_stack([rng.normal(1000, 100, 200), rng.normal(3, 1, 200)])

scaler = ot.utils.DataScaler(norm="standard").fit([X_s, X_t])
raw = ot.sliced.sliced_wasserstein_distance(X_s, X_t, n_projections=100, seed=0)
scaled = ot.sliced.sliced_wasserstein_distance(
    X_s, X_t, n_projections=100, seed=0, scaler=scaler
)
print({"raw": float(raw), "scaled": float(scaled)})
```

Use this when features are measured in different units. Do not fit a new scaler on each mini-batch if the value is used as a loss; fit on a representative reference sample and call `transform` consistently.

## 3. Build approximate sliced transport plans

Use sliced plans when the task needs an approximate plan but cannot afford dense exact OT at full scale. Start small because the returned plan is still `(n_source, n_target)` when `dense=True`.

```python
import numpy as np
import ot

rng = np.random.RandomState(2)
X_s = rng.normal(size=(20, 2))
X_t = rng.normal(loc=[1.0, -0.5], size=(25, 2))
a = rng.rand(X_s.shape[0]); a /= a.sum()
b = rng.rand(X_t.shape[0]); b /= b.sum()

projections = ot.sliced.get_random_projections(X_s.shape[1], 64, seed=0)
plan_min, cost_min, log_min = ot.sliced.min_sliced_transport_plan(
    X_s, X_t, a=a, b=b, projections=projections, dense=True, log=True
)
plan_exp, cost_exp = ot.sliced.expected_sliced_plan(
    X_s, X_t, a=a, b=b, projections=projections, beta=0.0, dense=True
)

assert np.allclose(plan_min.sum(axis=1), a)
assert np.allclose(plan_min.sum(axis=0), b)
assert np.allclose(plan_exp.sum(axis=1), a)
assert np.allclose(plan_exp.sum(axis=0), b)
print(float(cost_min), float(cost_exp), log_min["min_projection"].shape)
```

Selection rules:

- `min_sliced_transport_plan` keeps the best projected coupling under the chosen ground metric; it is sparse/permutation-like when weights and sample counts permit.
- `expected_sliced_plan` averages projected plans; `beta=0` weights projections uniformly, while very large `beta` approaches the min-sliced choice.
- `dense=False` can reduce memory under NumPy/SciPy by returning a sparse representation. Check downstream code before relying on sparse outputs.
- `batch_size` can limit memory during cost evaluation but does not make a final dense plan small.

## 4. Use spherical sliced distances

Use spherical sliced Wasserstein only when points represent directions or spherical data. Normalize first.

```python
import numpy as np
import ot

rng = np.random.RandomState(3)
X_s = rng.normal(size=(64, 3))
X_t = rng.normal(size=(64, 3))
X_s = X_s / np.linalg.norm(X_s, axis=1, keepdims=True)
X_t = X_t / np.linalg.norm(X_t, axis=1, keepdims=True)

d = ot.sliced.sliced_wasserstein_sphere(X_s, X_t, n_projections=50, seed=0)
d_unif = ot.sliced.sliced_wasserstein_sphere_unif(X_s, n_projections=50, seed=0)
print(float(d), float(d_unif))
```

Validation: every row norm should be close to one. If data are angles on a circle rather than points on a sphere, route to the 1-D/circle solver guidance in `core-solvers`.

## 5. Use `ot.solve_sample` as a high-level approximation router

When the caller prefers POT's unified result object, use `ot.solve_sample` with an approximation method and validate the result on small inputs.

```python
import numpy as np
import ot

rng = np.random.RandomState(4)
X_s = rng.normal(size=(30, 3))
X_t = rng.normal(loc=0.2, size=(35, 3))

res = ot.solve_sample(
    X_s, X_t,
    method="sliced",
    n_projections=64,
    random_state=0,
)
print(res.value)
```

Common approximation methods for this sub-skill:

| Method | Main knobs | Validate |
| --- | --- | --- |
| `"sliced"` / `"max_sliced"` | `n_projections`, `projections`, `random_state`, `scaler` | Repeat seeds; compare ordering against a tiny dense baseline. |
| `"lowrank"` | `rank`, `reg`, `scaling`, `random_state` | Check plan marginals if a plan is materialized; increase rank for accuracy. |
| `"nystroem"` | `rank`/anchors-like settings when exposed through the installed version | Compare with small Sinkhorn; check kernel approximation stability. |
| `"factored"` | `rank`/intermediate support size, `X_init` | Validate `Ga @ Gb` marginals on a small case if using the composed plan. |
| `"bsp"` | `n_projections`/plans, `random_state` | Equal sample counts; verify returned permutation is a bijection. |

If `solve_sample` does not expose a method in the installed version, call the lower-level module API from [api-reference.md](api-reference.md) instead.

## 6. Approximation validation checklist for large problems

Before replacing dense OT in a user workflow:

1. **Subsample baseline:** On `n <= 100` representative points, compute a dense reference in `core-solvers`; compare monotonic trends, marginal validity, or relative ranking, not exact equality.
2. **Budget knob sweep:** Sweep `n_projections`, rank, anchors, or `n_plans` over at least three values. Stop when the metric/plan statistic stabilizes relative to task tolerance.
3. **Randomness audit:** Fix seeds for reproducible runs. If conclusions change materially across seeds, report uncertainty and increase projections/rank/anchors.
4. **Mass check:** Any plan-like output should have row and column sums matching `a` and `b` within tolerance, unless the selected method is deliberately unbalanced or approximate in a different sense.
5. **Memory check:** Estimate `n_source * n_target * 8` bytes for every dense float64 plan or cost matrix. Use lazy/sparse/low-rank forms until a full plan is truly required.
6. **Failure route:** Use [troubleshooting.md](troubleshooting.md) for seed variance, covariance/GMM shape failures, low-rank convergence, optional dependencies, or memory errors.
