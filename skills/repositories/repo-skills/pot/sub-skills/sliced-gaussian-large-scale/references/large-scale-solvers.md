# Large-scale and structured solver selection

Use this reference when a dense cost matrix or dense transport plan is too expensive, or when the problem is structured enough to use a specialized POT solver. The methods below are approximations or specialized objectives; validate them against task needs rather than assuming exact OT equivalence.

## Solver selection matrix

| Need | Preferred family | Main API | Inputs | Output | Main knobs | Caveats |
| --- | --- | --- | --- | --- | --- | --- |
| Fast scalar discrepancy between sample clouds | Sliced Wasserstein | `ot.sliced.sliced_wasserstein_distance` | `(n, d)` samples and optional weights | Scalar | `n_projections`, `seed`, `p`, `scaler` | Monte Carlo variance; no dense plan. |
| Approximate plan from random projections | Sliced plans | `min_sliced_transport_plan`, `expected_sliced_plan` | Samples and optional weights | Plan plus cost | `n_projections`, `beta`, `dense`, `batch_size` | Dense plan can still be large. |
| Low-rank entropic coupling | Low-rank Sinkhorn | `ot.lowrank.lowrank_sinkhorn` | Samples, weights | Factors `Q`, `R`, `g`; lazy plan in log | `rank`, `reg`, `alpha`, `init`, `numItermax` | Materializing `lazy_plan[:]` is dense. |
| Gaussian-kernel Sinkhorn acceleration | Nystroem | `kernel_nystroem` + `sinkhorn_low_rank_kernel` | Samples or precomputed kernel factors | Scaling vectors/lazy plan | `anchors`, `sigma`, `numItermax` | Anchor quality controls accuracy. |
| Sparse intermediate support | Factored OT | `ot.factored.factored_optimal_transport` | Samples and weights | `Ga`, `Gb`, intermediate support | `r`, `reg`, `X0`, iterations | CPU C++ backend may copy GPU arrays. |
| Equal-size bijection | BSP-OT | `ot.bsp.compute_bspot_bijection` | Same-size point clouds | Cost, permutation, candidate permutations | `n_plans`, `p`, `gaussian_slicing`, `seed` | No optimality guarantee; build needs compiled extension. |
| Continuous source to atomic target | Semidiscrete OT | `ot.semidiscrete.solve_semidiscrete` | Target atoms plus source sampler | Semi-dual potential, maps/weights | `batch_size`, `max_iter`, `lr0`, `reg`, `max_cost` | Stochastic convergence; sampler quality matters. |
| Large regularized discrete OT by stochastic optimization | Stochastic dual/semidual | `ot.stochastic.solve_*` | Histograms and cost matrix | Approximate plan/logs | `batch_size`, `lr`, `numItermax`, `reg` | Sensitive to learning rate and regularization. |
| Compare spectral operators | SGOT | `ot.sgot.sgot_metric` | Eigenvalues and left/right eigenspaces | Distance/cost matrix | `eta`, `p`, `q`, `r`, `grassmann_metric` | Shape-heavy; only meaningful for spectral atoms. |
| Align matrix rows and columns | COOT | `ot.coot.co_optimal_transport` | Matrices and row/feature weights | Sample and feature couplings | `epsilon`, `alpha`, warmstart, BCD iterations | Objective differs from ordinary sample OT. |
| 1-D grid multi-marginal Monge notes | DMMOT | `ot.lp.dmmot_monge_1dgrid_optimize` | Distributions as columns on shared grid | Optimized distributions/logs | `niters`, `lr_init`, `lr_decay` | Objective differs from LP barycenter; 1-D grid only. |

## Memory sizing rules

- Dense cost or plan: approximately `n_source * n_target * 8` bytes for float64, before overhead.
- Sliced distance: avoids dense cost/plan, but repeated projections cost `O(n_projections * (n log n + m log m))` plus projection work.
- Sliced plan with `dense=True`: still returns an `(n_source, n_target)` object.
- Low-rank factors: store roughly `(n_source + n_target) * rank + rank` values, but calling `lazy_plan[:]` materializes a dense plan.
- BSP permutation: stores an index vector of length `n` and candidate permutations; useful only for equal-size point clouds.
- COOT: maintains separate sample and feature couplings; large matrices can still be expensive in both dimensions.

## Low-rank Sinkhorn workflow

```python
import numpy as np
import ot

n = 80
X_s = np.linspace(0.0, 1.0, n)[:, None]
X_t = np.linspace(0.1, 1.1, n)[:, None]
a = ot.unif(n)
b = ot.unif(n)

Q, R, g, log = ot.lowrank.lowrank_sinkhorn(
    X_s, X_t, a=a, b=b, reg=0.1, rank=8,
    init="deterministic", rescale_cost=False, warn=False, log=True
)
# Only materialize on small cases.
P = log["lazy_plan"][:]
assert np.allclose(P.sum(axis=1), a, atol=1e-5)
assert np.allclose(P.sum(axis=0), b, atol=1e-5)
print(log["value_linear"])
```

Practical knobs:

- Increase `rank` for accuracy and memory use.
- `reg > 0` improves numerical stability; very small `reg` may behave like hard OT and converge slowly.
- `alpha` must stay below `1 / rank`; invalid values raise `ValueError`.
- `init="kmeans"` requires scikit-learn. Use `"random"` or `"deterministic"` in minimal environments.

## Nystroem kernel workflow

```python
import math
import numpy as np
import ot

rng = np.random.RandomState(0)
X_s = rng.normal(size=(30, 2))
X_t = rng.normal(loc=1.0, size=(30, 2))
reg = 2.0
K1, K2 = ot.lowrank.kernel_nystroem(
    X_s, X_t, anchors=12, sigma=math.sqrt(reg / 2.0), random_state=0
)
u, v, log = ot.lowrank.sinkhorn_low_rank_kernel(K1, K2, log=True, warn=False)
P_small = log["lazy_plan"][:]
print(K1.shape, K2.shape, P_small.shape)
```

Use more anchors when the approximation is unstable. If `anchors` is too small, use a larger value and validate against a small dense Sinkhorn plan.

## Factored OT workflow

```python
import numpy as np
import ot

rng = np.random.RandomState(1)
X_s = rng.rand(40, 2)
X_t = rng.rand(50, 2) + np.array([0.5, 0.0])
a = ot.unif(X_s.shape[0])
b = ot.unif(X_t.shape[0])
Ga, Gb, X_mid = ot.factored.factored_optimal_transport(X_s, X_t, a=a, b=b, r=6)
assert Ga.shape == (X_s.shape[0], 6)
assert Gb.shape == (6, X_t.shape[0])
assert X_mid.shape == (6, X_s.shape[1])
```

The composed plan `Ga @ Gb` is dense if materialized. Keep the factorization unless downstream code truly needs the full plan.

## BSP-OT bijection workflow

```python
import numpy as np
import ot

rng = np.random.RandomState(2)
X = rng.normal(size=(64, 2))
Y = 1.5 * X + np.array([0.25, -0.1])
cost, perm, candidate_perms = ot.bsp.compute_bspot_bijection(
    X, Y, n_plans=8, p=2, seed=0
)
assert sorted(perm.tolist()) == list(range(X.shape[0]))
Y_aligned = Y[perm]
print(float(cost), candidate_perms.shape, Y_aligned.shape)
```

Use BSP when the task needs a bijection/permutation between equal-size clouds. It is fast and scalable but approximate; verify with a small exact baseline when quality matters. If building POT from source fails at BSP import/build time, the compiled extension may need its C++/Eigen dependency; route installation repair to `backend-and-batch` or root troubleshooting.

## Semidiscrete OT workflow

Semidiscrete OT maps a continuous source distribution, sampled by a callable or built-in sampler, to finitely many target atoms.

```python
import numpy as np
from ot.semidiscrete import solve_semidiscrete, semidiscrete_atom_weights, semidiscrete_ot_map

rng = np.random.default_rng(0)
target = np.array([[0.25, 0.25], [0.75, 0.25], [0.5, 0.75]])

def sampler(batch_size):
    return rng.random((batch_size, 2))

g = solve_semidiscrete(
    target, sampler_source=sampler, max_iter=500, batch_size=16,
    max_cost=2.0, decreasing_reg=True
)
probe = sampler(32)
weights = semidiscrete_atom_weights(target, probe, g, reg=0.0)
mapped = semidiscrete_ot_map(target, probe, g, reg=0.0)
assert np.allclose(weights.sum(axis=1), 1.0)
print(g.shape, mapped.shape)
```

For reliable runs, increase `max_iter`, tune `batch_size`, set `max_cost` from an upper bound on the ground cost, and check empirical cell masses.

## Stochastic dual and semidual workflow

```python
import numpy as np
import ot

rng = np.random.RandomState(3)
X_s = rng.normal(size=(7, 2))
X_t = rng.normal(size=(5, 2))
a = ot.unif(X_s.shape[0])
b = ot.unif(X_t.shape[0])
M = ot.dist(X_s, X_t)

pi_sag = ot.stochastic.solve_semi_dual_entropic(a, b, M, reg=1.0, method="SAG", numItermax=500)
pi_sgd = ot.stochastic.solve_dual_entropic(a, b, M, reg=1.0, batch_size=3, numItermax=1000, lr=0.1)
assert pi_sag.shape == M.shape
assert pi_sgd.shape == M.shape
```

These solvers are useful for large-scale regularized OT experiments but are sensitive to `lr`, `batch_size`, and `reg`. Compare to Sinkhorn on a tiny problem before using them as a replacement.

## SGOT workflow for spectral operators

```python
import numpy as np
import ot

rng = np.random.RandomState(4)
r = 3
d = 5
Ds = rng.normal(size=r) + 1j * rng.normal(size=r)
Dt = Ds + 0.1
Rs = rng.normal(size=(d, r)) + 1j * rng.normal(size=(d, r))
Ls = Rs.copy()
Rt = Rs + 0.05 * (rng.normal(size=(d, r)) + 1j * rng.normal(size=(d, r)))
Lt = Rt.copy()

C = ot.sgot.sgot_cost_matrix(Ds, Rs, Ls, Dt, Rt, Lt, eta=0.5, grassmann_metric="chordal")
dist = ot.sgot.sgot_metric(Ds, Rs, Ls, Dt, Rt, Lt, eta=0.5, grassmann_metric="chordal")
assert C.shape == (r, r)
assert np.isfinite(dist)
```

Allowed `grassmann_metric` values are `"geodesic"`, `"chordal"`, `"procrustes"`, and `"martin"`. Eigenvalue vectors must be one-dimensional; left/right eigenvector matrices must have compatible `(ambient_dim, rank)` shapes.

## COOT workflow for matrix row/feature alignment

```python
import numpy as np
import ot

rng = np.random.RandomState(5)
X = rng.normal(size=(12, 6))
Y = X[::-1, ::-1].copy()
pi_sample, pi_feature, log = ot.coot.co_optimal_transport(
    X, Y, epsilon=(0.1, 0.1), nits_bcd=20, nits_ot=200, log=True
)
coot_value = ot.coot.co_optimal_transport2(X, Y, epsilon=(0.1, 0.1), nits_bcd=20, nits_ot=200)
assert pi_sample.shape == (X.shape[0], Y.shape[0])
assert pi_feature.shape == (X.shape[1], Y.shape[1])
print(float(coot_value), log.keys())
```

Use `epsilon` and `alpha` as scalars or length-2 values for sample/feature couplings. If `epsilon=0`, POT can use exact EMD internally; nonzero entropic regularization is usually smoother.

## DMMOT notes for one-dimensional grid distributions

DMMOT helpers are for one-dimensional distributions on a shared grid and optimize a Monge multi-marginal objective. Do not compare its objective values directly with LP barycenter objectives.

```python
import numpy as np
import ot

n = 30
x = np.arange(n, dtype=float)
a1 = ot.datasets.make_1D_gauss(n, m=8, s=3)
a2 = ot.datasets.make_1D_gauss(n, m=20, s=4)
A = np.vstack([a1, a2]).T
barys, log = ot.lp.dmmot_monge_1dgrid_optimize(A, niters=100, lr_init=1e-5, log=True)
print(np.asarray(barys).shape, log.keys())
```

Use this only when the data match the one-dimensional shared-grid assumption. For ordinary barycenters, route to `barycenters`.
