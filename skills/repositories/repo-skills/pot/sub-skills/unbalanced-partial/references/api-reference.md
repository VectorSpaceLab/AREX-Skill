# Unbalanced and partial OT API reference

This reference is for choosing POT APIs and parameters for relaxed-marginal or partial-mass workflows. It assumes POT is importable as `ot` and NumPy arrays are available.

## Minimal import check

```bash
python - <<'PY'
import numpy as np
import ot
print("POT", getattr(ot, "__version__", "unknown"))
print("numpy fixture", np.array([0.5, 0.5]).sum())
PY
```

The minimum backend verified for this generated skill was NumPy. PyTorch, JAX, TensorFlow, CuPy, plotting, and other optional extras are optional and should be treated as unverified unless separately checked in the target environment.

## Data conventions

- `a` and `b` are one-dimensional nonnegative histograms aligned with the rows and columns of `M`. They may be unnormalized for UOT and partial OT, but partial mass `m` must satisfy `0 <= m <= min(a.sum(), b.sum())`.
- `M` is a finite cost matrix of shape `(len(a), len(b))`. For sample clouds, compute it with `ot.dist(Xs, Xt)` or a user-chosen metric before calling these solvers.
- Cost scaling matters. If `M` is divided by `M.max()`, values such as `reg=0.05` and `reg_m=0.2` are on the normalized scale; do not reuse those numbers blindly on unscaled costs.
- Empty histograms (`np.array([])`) mean uniform weights for several POT solvers. Use explicit weights in production workflows to avoid accidental defaults.
- Negative weights, NaNs, or mismatched dimensions are user-data errors; fix them before solving rather than interpreting solver output.

## Solver selection matrix

| Need | Primary API | Main parameters | Return and validation |
| --- | --- | --- | --- |
| Entropic UOT with KL marginal relaxation | `ot.unbalanced.sinkhorn_unbalanced` | `reg > 0`, `reg_m`, `method`, `reg_type` | Plan `G`; check `G.shape == M.shape`, finite values, and relaxed row/column sums. |
| Entropic UOT cost only | `ot.unbalanced.sinkhorn_unbalanced2` | same as above plus `returnCost` | Cost scalar or vector; `returnCost="linear"` is transport cost, `"total"` adds regularization and marginal penalties. |
| Non-entropic UOT with KL or L2 marginal penalties | `ot.unbalanced.mm_unbalanced` | `reg_m`, optional `reg`, `div="kl"` or `"l2"` | Plan `G`; high `reg_m` approaches balanced marginals, low `reg_m` allows mass deletion/creation. |
| Non-entropic UOT cost only | `ot.unbalanced.mm_unbalanced2` | same as above plus `returnCost` | Cost scalar; useful for parameter sweeps. |
| Generic SciPy optimizer for KL/L2/TV marginal penalties or custom regularization | `ot.unbalanced.lbfgsb_unbalanced` | `reg`, `reg_m`, `reg_div`, `regm_div` | Plan `G`; converts through NumPy and can be slower but supports `regm_div="tv"`. |
| Exact partial OT with fixed transported mass | `ot.partial.partial_wasserstein` | `m`, `nb_dummies` | Plan `G`; validate `G.sum() == m`, `G.sum(1) <= a`, `G.sum(0) <= b`. |
| Exact partial OT cost | `ot.partial.partial_wasserstein2` | `m`, `nb_dummies` | Scalar cost; with `log=True`, `log["T"]` stores the plan. |
| Entropic partial OT | `ot.partial.entropic_partial_wasserstein` | `reg`, `m`, `method` | Plan `G`; use `method="sinkhorn_log"` when small `reg` or large costs risk underflow. |
| Stable log-domain entropic partial OT | `ot.partial.entropic_partial_wasserstein_logscale` | `reg`, `m` | Same plan format as entropic partial; slower but more stable at small `reg`. |
| 1D partial OT over unweighted point sets | `ot.partial.partial_wasserstein_1d` | `n_transported_samples`, `p` | Indices into `x_a`, indices into `x_b`, and marginal costs for intermediate partial plans. |
| 1D KL-UOT with autodiff backend | `ot.unbalanced.uot_1d` | `reg_m`, optional weights, `p`, `returnCost` | Reweighted marginals and loss; requires PyTorch or JAX arrays, not plain NumPy arrays. |
| Fixed-grid unbalanced barycenter | `ot.unbalanced.barycenter_unbalanced` | `A`, square `M`, `reg`, `reg_m`, `weights` | Barycenter vector; total mass is not forced to equal each input mass. |
| L2-UOT regularization path | `ot.regpath.regularization_path`, `ot.regpath.compute_transport_plan` | `reg`, `semi_relaxed`, `gamma` | Flattened plans along a piecewise-linear path; reshape to `M.shape` before validating marginals. |
| Unified linear solver route | `ot.solve` | `unbalanced`, `unbalanced_type`, optional `reg`, `reg_type` | `OTResult` with `.plan`; use this when you want unified routing rather than a specialized UOT/partial function. |

## Verified signatures and defaults

```text
ot.unbalanced.sinkhorn_unbalanced(a, b, M, reg, reg_m, method='sinkhorn', reg_type='kl', c=None, warmstart=None, numItermax=1000, stopThr=1e-06, verbose=False, log=False, **kwargs)
ot.unbalanced.sinkhorn_unbalanced2(a, b, M, reg, reg_m, method='sinkhorn', reg_type='kl', c=None, warmstart=None, returnCost='linear', numItermax=1000, stopThr=1e-06, verbose=False, log=False, **kwargs)
ot.unbalanced.mm_unbalanced(a, b, M, reg_m, c=None, reg=0, div='kl', G0=None, numItermax=1000, stopThr=1e-15, verbose=False, log=False)
ot.unbalanced.mm_unbalanced2(a, b, M, reg_m, c=None, reg=0, div='kl', G0=None, returnCost='linear', numItermax=1000, stopThr=1e-15, verbose=False, log=False)
ot.unbalanced.lbfgsb_unbalanced(a, b, M, reg, reg_m, c=None, reg_div='kl', regm_div='kl', G0=None, numItermax=1000, stopThr=1e-15, method='L-BFGS-B', verbose=False, log=False)
ot.unbalanced.lbfgsb_unbalanced2(a, b, M, reg, reg_m, c=None, reg_div='kl', regm_div='kl', G0=None, returnCost='linear', numItermax=1000, stopThr=1e-15, method='L-BFGS-B', verbose=False, log=False)
ot.unbalanced.uot_1d(u_values, v_values, reg_m, u_weights=None, v_weights=None, p=2, require_sort=True, numItermax=10, returnCost='linear', log=False)
ot.unbalanced.barycenter_unbalanced(A, M, reg, reg_m, method='sinkhorn', weights=None, numItermax=1000, stopThr=1e-06, verbose=False, log=False, **kwargs)
ot.partial.partial_wasserstein(a, b, M, m=None, nb_dummies=1, log=False, **kwargs)
ot.partial.partial_wasserstein2(a, b, M, m=None, nb_dummies=1, log=False, **kwargs)
ot.partial.entropic_partial_wasserstein(a, b, M, reg, m=None, method='sinkhorn', numItermax=1000, stopThr=1e-100, verbose=False, log=False)
ot.partial.entropic_partial_wasserstein_logscale(a, b, M, reg, m=None, numItermax=1000, stopThr=1e-100, verbose=False, log=False)
ot.partial.partial_wasserstein_1d(x_a, x_b, n_transported_samples=None, p=1)
ot.regpath.regularization_path(a, b, C, reg=0.0001, semi_relaxed=False, itmax=50000)
ot.regpath.compute_transport_plan(gamma, gamma_list, Pi_list)
```

Gromov-related entry points are routed here only at the mass-semantics level. Use the `gromov` sub-skill for GW modeling details.

```text
ot.gromov.partial_gromov_wasserstein(C1, C2, p=None, q=None, m=None, loss_fun='square_loss', nb_dummies=1, G0=None, thres=1, numItermax=10000.0, tol=1e-08, symmetric=None, warn=True, log=False, verbose=False, **kwargs)
ot.gromov.entropic_partial_gromov_wasserstein(C1, C2, p=None, q=None, reg=1.0, m=None, loss_fun='square_loss', G0=None, numItermax=1000, tol=1e-07, symmetric=None, log=False, verbose=False)
ot.gromov.fused_unbalanced_gromov_wasserstein(Cx, Cy, wx=None, wy=None, reg_marginals=10, epsilon=0, divergence='kl', unbalanced_solver='mm', alpha=0, M=None, init_duals=None, init_pi=None, max_iter=100, tol=1e-07, max_iter_ot=500, tol_ot=1e-07, log=False, verbose=False, **kwargs_solve)
ot.gromov.unbalanced_co_optimal_transport(X, Y, wx_samp=None, wx_feat=None, wy_samp=None, wy_feat=None, reg_marginals=10, epsilon=0, divergence='kl', unbalanced_solver='mm', alpha=0, M_samp=None, M_feat=None, rescale_plan=True, init_pi=None, init_duals=None, max_iter=100, tol=1e-07, max_iter_ot=500, tol_ot=1e-07, log=False, verbose=False, **kwargs_solve)
```

## Parameter semantics

### `reg` versus `reg_m` / `unbalanced`

- `reg` regularizes the transport plan itself. In entropic solvers it controls smoothness and numerical scale of kernels such as `exp(-M / reg)`.
- `reg_m` in specialized APIs, and `unbalanced` in `ot.solve`, penalize deviation from the supplied marginals. Larger values enforce marginals more strongly. Smaller values allow more mass deletion/creation.
- `reg_m` may be a scalar or a pair `(source_penalty, target_penalty)` for many UOT solvers. Use `(float("inf"), value)` or `(value, float("inf"))` only where the API documents semi-relaxed support, such as entropic UOT or `uot_1d`; MM and L-BFGS-B UOT do not accept infinite marginal relaxation.

### Divergence names

- `sinkhorn_unbalanced` uses `reg_type="kl"` by default. It also accepts `"entropy"` for the plan regularizer.
- `mm_unbalanced` uses `div="kl"` or `div="l2"` for marginal relaxation.
- `lbfgsb_unbalanced` separates `reg_div` for plan regularization (`"entropy"`, `"kl"`, `"l2"`, or a callable pair) from `regm_div` for marginals (`"kl"`, `"l2"`, `"tv"`).
- Unified `ot.solve` uses `unbalanced_type="KL"`, `"L2"`, or `"TV"` for linear OT. For Gromov workflows, `unbalanced_type="partial"` and semirelaxed routes belong to the `gromov` sub-skill.

### Partial transported mass `m`

- `m=None` means the largest feasible transported mass for partial solvers, usually `min(a.sum(), b.sum())`.
- `m` is an absolute mass, not a fraction, unless `a` and `b` both sum to one. If weights are unnormalized, compute `m` on the same scale as the weights.
- Exact partial solvers return sparse-looking plans and may use dummy points internally. Entropic partial solvers return smoother plans and require `reg > 0`.

## Validation snippets

Check a partial plan:

```python
G = ot.partial.partial_wasserstein(a, b, M, m=m)
assert G.shape == M.shape
assert np.isfinite(G).all()
assert np.all(G >= -1e-12)
assert abs(G.sum() - m) < 1e-8
assert np.all(G.sum(axis=1) <= a + 1e-8)
assert np.all(G.sum(axis=0) <= b + 1e-8)
```

Check a UOT plan:

```python
G = ot.unbalanced.mm_unbalanced(a, b, M, reg_m=0.2, div="kl")
assert G.shape == M.shape
assert np.isfinite(G).all()
assert np.all(G >= -1e-12)
transported_mass = float(G.sum())
row_relaxation = G.sum(axis=1) - a
col_relaxation = G.sum(axis=0) - b
```

Use the bundled smoke helper for a complete deterministic check:

```bash
python scripts/unbalanced_partial_smoke.py --case all
```
