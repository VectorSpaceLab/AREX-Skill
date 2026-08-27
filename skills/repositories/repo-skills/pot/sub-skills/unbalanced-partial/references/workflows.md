# Unbalanced and partial OT workflows

Use these recipes when a task asks for unequal masses, outlier rejection, fixed transported mass, unbalanced barycenters, 1D partial/UOT helpers, or UOT regularization paths.

## Start with the bundled smoke helper

From this sub-skill directory, run:

```bash
python scripts/unbalanced_partial_smoke.py --case all
```

Expected signal: the helper exits zero and prints `passed` status lines for deterministic 2D UOT, fixed-mass partial OT plus 1D partial OT, unbalanced barycenter, and L2-UOT regularization-path checks. Use `--json` for machine-readable output:

```bash
python scripts/unbalanced_partial_smoke.py --case all --json
```

The legacy optional `uot_1d` check is not run by default because POT requires an autodiff backend for that function. When requested, the helper attempts a PyTorch-backed fixture and records a structured skip instead of failing a NumPy-only environment:

```bash
python scripts/unbalanced_partial_smoke.py --case all --include-optional-uot-1d --json
```

## Workflow 1: compare UOT and partial OT for outliers

Use this when distributions mostly match but each side has extra outlier mass. UOT chooses reweighted marginals through a penalty; partial OT transports exactly `m` and can leave the rest unused.

```python
import numpy as np
import ot

Xs = np.array([[0.0, 0.0], [0.1, 0.0], [-0.1, 0.0], [5.0, 5.0]])
Xt = np.array([[0.05, 0.0], [-0.05, 0.0], [0.0, 0.1], [-5.0, -5.0]])
a = np.array([0.30, 0.30, 0.30, 0.10])
b = np.array([0.25, 0.25, 0.25, 0.25])
M = ot.dist(Xs, Xt)
M = M / M.max()

m = 0.75
G_partial = ot.partial.partial_wasserstein(a, b, M, m=m)
G_uot_l2 = ot.unbalanced.mm_unbalanced(a, b, M, reg_m=0.2, div="l2")
G_uot_kl = ot.unbalanced.sinkhorn_unbalanced(
    a, b, M, reg=0.05, reg_m=0.2, method="sinkhorn", reg_type="kl"
)

for name, G in [("partial", G_partial), ("l2-uot", G_uot_l2), ("kl-entropic-uot", G_uot_kl)]:
    print(name, "mass", float(G.sum()), "source rows", G.sum(axis=1), "target cols", G.sum(axis=0))
```

Validation checklist:

1. `G_partial.sum()` should match `m` and `G_partial.sum(1) <= a`, `G_partial.sum(0) <= b`.
2. UOT plans need not sum to `m` or to either total marginal mass. Inspect row/column sums to see which atoms were downweighted.
3. If outliers are still used too much, decrease `m` for partial OT or decrease `reg_m` for UOT. If too much normal mass is discarded, increase `m` or `reg_m`.
4. If results change dramatically after scaling `M`, tune `reg` and `reg_m` on the new cost scale.

This workflow is a synthetic difficult case for later verification because it asks the skill to explain the modeling difference between relaxed marginals and fixed transported mass, not just reproduce a single solver output.

## Workflow 2: avoid NaNs in entropic partial OT at small `reg`

Use exact partial OT when you need a sparse plan and the problem size is small enough. Use entropic partial OT when a smoother differentiable-like plan is acceptable. At small `reg` or large cost scale, prefer the log-domain method.

```python
import numpy as np
import ot

rng = np.random.RandomState(1)
n = 30
a = rng.rand(n); a /= a.sum()
b = rng.rand(n); b /= b.sum()
M = ot.dist(rng.rand(n, 2), rng.rand(n, 2)) * 50.0
m = 0.6

G = ot.partial.entropic_partial_wasserstein(
    a, b, M, reg=0.01, m=m, method="sinkhorn_log", numItermax=3000
)
assert np.isfinite(G).all()
assert abs(G.sum() - m) < 5e-3
```

Recovery steps when the classical method fails:

1. Confirm `m <= min(a.sum(), b.sum())`.
2. Use `method="sinkhorn_log"` or call `ot.partial.entropic_partial_wasserstein_logscale` directly.
3. Increase `numItermax` before loosening mass tolerance.
4. If speed is unacceptable, increase `reg`, rescale `M`, or switch to exact `partial_wasserstein` for small dense problems.

This workflow covers the difficult usability case where a user gets NaNs in entropic partial OT at small regularization.

## Workflow 3: unified `ot.solve` variants for unbalanced linear OT

Use specialized APIs when you need full control over UOT or partial solver internals. Use `ot.solve` when a task already uses POT's unified result object and only needs to change the mass model.

```python
import numpy as np
import ot

x = np.arange(6, dtype=float)[:, None]
a = np.array([0.10, 0.20, 0.25, 0.20, 0.15, 0.10])
b = np.array([0.05, 0.15, 0.20, 0.20, 0.20, 0.20])
M = ot.dist(x, x)
M = M / M.max()

res_kl = ot.solve(M, a, b, unbalanced=0.5, unbalanced_type="KL")
res_l2 = ot.solve(M, a, b, unbalanced=0.5, unbalanced_type="L2")
res_tv = ot.solve(M, a, b, unbalanced=0.2, unbalanced_type="TV")
for res in [res_kl, res_l2, res_tv]:
    assert res.plan.shape == M.shape
    assert np.isfinite(res.plan).all()
```

Routing notes:

- `unbalanced_type="KL"` and `"L2"` map to unbalanced OT. `"TV"` acts like a partial/sparsity-inducing marginal penalty.
- Balanced exact/Sinkhorn setup and `OTResult` fundamentals belong to `core-solvers`; this section only records how to set unbalanced arguments.
- For Gromov workflows, `ot.solve_gromov(..., unbalanced_type="partial", unbalanced=m)` is routed to `gromov` after confirming partial mass semantics here.

## Workflow 4: unbalanced fixed-grid barycenter

Use `barycenter_unbalanced` when histograms live on the same support but have different masses.

```python
import numpy as np
import ot

x = np.arange(5, dtype=float)[:, None]
M = ot.dist(x, x)
M = M / M.max()
a1 = np.array([0.05, 0.15, 0.60, 0.15, 0.05])
a2 = 1.8 * np.array([0.05, 0.10, 0.20, 0.40, 0.25])
A = np.vstack([a1, a2]).T  # columns are histograms
weights = np.array([0.4, 0.6])

bary = ot.unbalanced.barycenter_unbalanced(A, M, reg=0.1, reg_m=1.0, weights=weights)
assert bary.shape == (M.shape[0],)
assert np.isfinite(bary).all()
assert np.all(bary >= -1e-12)
print("barycenter total mass", float(bary.sum()))
```

Validation steps:

- `A.shape == (dim, n_hists)`; columns are histograms.
- `M.shape == (dim, dim)` and uses the same support as rows of `A`.
- `weights` has one value per histogram and should sum to one for barycentric interpretation.
- The barycenter mass is itself optimized; do not expect it to equal each input mass.

## Workflow 5: L2-UOT regularization path

Use `ot.regpath` when the user asks how L2-unbalanced plans evolve as the marginal penalty changes.

```python
import numpy as np
import ot

Xs = np.array([[0.0], [1.0], [3.0]])
Xt = np.array([[0.2], [1.5], [2.5]])
a = np.array([0.2, 0.5, 0.3])
b = np.array([0.3, 0.4, 0.3])
M = ot.dist(Xs, Xt)
M = M / M.max()

t, plan_path, gamma_path = ot.regpath.regularization_path(
    a, b, M, reg=1e-4, semi_relaxed=False, itmax=1000
)
G_gamma = ot.regpath.compute_transport_plan(1.0, gamma_path, plan_path).reshape(M.shape)
assert G_gamma.shape == M.shape
assert np.isfinite(G_gamma).all()
print("path knots", len(gamma_path), "mass at gamma=1", float(G_gamma.sum()))
```

Interpretation:

- `gamma` is the inverse-style coefficient used by the Lasso reformulation of L2-UOT; larger/smaller values can change transported mass and sparsity.
- `semi_relaxed=True` fixes one marginal and relaxes the other according to the semi-relaxed formulation.
- Plans from the path are flattened; reshape them to `M.shape` before interpreting marginals.

## Workflow 6: 1D partial OT and optional 1D UOT

For unweighted 1D partial matching, use NumPy arrays with `partial_wasserstein_1d`:

```python
import numpy as np
import ot

x = np.array([5.0, -2.0, 4.0])
y = np.array([-1.0, 1.0, 3.0])
ind_x, ind_y, marginal_costs = ot.partial.partial_wasserstein_1d(
    x, y, n_transported_samples=2, p=1
)
print(ind_x, ind_y, np.cumsum(marginal_costs))
```

For `ot.unbalanced.uot_1d`, POT requires PyTorch or JAX arrays because the solver uses autodifferentiation for potentials. In a NumPy-only environment, do not call it as if it were a NumPy solver; either install/verify a supported backend or use a matrix UOT solver such as `mm_unbalanced` on a 1D cost matrix.

Optional PyTorch-style pattern:

```python
import torch
import ot

x = torch.linspace(0, 1, 5, dtype=torch.float64)[:, None]
y = torch.linspace(0.1, 1.1, 5, dtype=torch.float64)[:, None]
a = torch.ones(5, dtype=torch.float64) / 5
b = torch.tensor([0.10, 0.15, 0.20, 0.25, 0.30], dtype=torch.float64)
u_reweighted, v_reweighted, loss = ot.unbalanced.uot_1d(x, y, reg_m=1.0, u_weights=a, v_weights=b, p=2)
```

Validation: `u_reweighted` and `v_reweighted` are the relaxed transported marginals; compare their sums and support concentration rather than expecting a dense transport matrix.

## Source-script adaptation notes

The bundled smoke helper adapts the numeric cores of POT's unbalanced/partial 2D examples, 1D partial example, unbalanced barycenter example, and regularization-path example. Plotting, animation, long sweeps, optional sliced-UOT visualization, and optional PyTorch/JAX runs are excluded from the default helper to keep runtime deterministic and self-contained.
