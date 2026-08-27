# Unbalanced and partial OT troubleshooting

Use this reference when POT unbalanced/partial solvers reject inputs, return unexpected transported mass, produce NaNs, or appear to ignore outliers incorrectly.

## Fast diagnostic command

Run the bundled helper first to separate installation problems from user-data or parameter problems:

```bash
python scripts/unbalanced_partial_smoke.py --case all
```

If this fails with a `Missing required dependency 'POT'` message, install the public package in the active environment and rerun:

```bash
python -m pip install POT
python scripts/unbalanced_partial_smoke.py --case all
```

If optional `uot_1d` is requested and the helper records a `skipped` status because an autodiff backend is missing, install and verify PyTorch or JAX separately before using `ot.unbalanced.uot_1d`.

## Symptom-to-recovery matrix

| Symptom | Likely cause | Recovery | Validate |
| --- | --- | --- | --- |
| `ValueError` says `m` should be greater than 0 or lower/equal than `min(|a|_1, |b|_1)` | Partial transported mass is infeasible. | Compute `m` on the same scale as `a` and `b`: `m = fraction * min(a.sum(), b.sum())` only when a fraction is intended. | `0 <= m <= min(a.sum(), b.sum())`; after solving, `abs(G.sum() - m)` is small. |
| Partial plan transports too much outlier mass | `m` is too high or costs do not separate outliers. | Lower `m`, rescale/inspect `M`, or use UOT with a smaller `reg_m` to softly downweight outliers. | Check row/column sums for outlier indices. |
| UOT plan mass is not equal to `a.sum()` or `b.sum()` | This is expected: UOT relaxes marginals. | Interpret `G.sum(1)` and `G.sum(0)` as reweighted transported marginals. Increase `reg_m` to enforce original marginals more strongly. | Compare `G.sum(1) - a` and `G.sum(0) - b`. |
| UOT behaves almost balanced | `reg_m`/`unbalanced` is very large relative to the cost scale. | Decrease `reg_m` or normalize `M` before tuning. | Transported row/column sums should move away from exact marginals as relaxation increases. |
| UOT deletes too much useful mass | `reg_m` is too small, `reg` is too small/large for the cost scale, or costs are poorly scaled. | Increase `reg_m`; if entropic, sweep `reg`; inspect costs between known matching points. | Relevant row/column sums become closer to input weights. |
| `Unknown div` in `mm_unbalanced` | `div` is not one of `"kl"` or `"l2"`. | Use `div="kl"` for KL marginal relaxation or `div="l2"` for half-squared L2 relaxation. For TV use `lbfgsb_unbalanced(..., regm_div="tv")` or unified `ot.solve(..., unbalanced_type="TV")`. | A tiny call with the chosen divergence returns a finite plan. |
| `Unknown reg_div` or `Unknown regm_div` in L-BFGS-B | Divergence name belongs to another solver or is misspelled. | `reg_div`: `"entropy"`, `"kl"`, `"l2"`, or a pair of NumPy-compatible callables. `regm_div`: `"kl"`, `"l2"`, `"tv"`. | Re-run with `log=True` and inspect `log["cost"]`, `log["total_cost"]`. |
| Unified `ot.solve` rejects `unbalanced_type` | Mixed names from specialized APIs. | Use `unbalanced_type="KL"`, `"L2"`, or `"TV"` for linear OT. Use `div` only with `mm_unbalanced`; use `regm_div` only with `lbfgsb_unbalanced`. | `res = ot.solve(M, a, b, unbalanced=value, unbalanced_type="KL")` has finite `res.plan`. |
| Entropic partial OT returns NaN/Inf at small `reg` | Classical multiplicative-domain kernel underflow, especially when `M / reg` is large. | Switch to `ot.partial.entropic_partial_wasserstein(..., method="sinkhorn_log")` or call `entropic_partial_wasserstein_logscale`. Increase `numItermax`, rescale costs, or increase `reg`. | `np.isfinite(G).all()` and `abs(G.sum() - m)` within tolerance. |
| Entropic partial OT is slow with `method="sinkhorn_log"` | Log-domain iterations trade speed for stability. | Use the classical method at larger `reg`, or exact `partial_wasserstein` for small problems where a sparse exact plan is acceptable. | Compare plan cost and mass at a safer `reg` before using a smaller one. |
| Exact partial OT raises an EMD dummy-point error | Internal dummy reservoirs are numerically unstable for this problem. | Increase `nb_dummies` in `partial_wasserstein` or `partial_wasserstein2`; consider entropic partial OT if exact EMD remains unstable. | Plan is finite and satisfies partial constraints. |
| `uot_1d` raises an assertion saying the function is only valid in torch/jax | The input arrays are NumPy or another unsupported backend. | Use PyTorch/JAX arrays and verify that backend, or use `mm_unbalanced`/`sinkhorn_unbalanced` on a 1D cost matrix instead. | Optional smoke: `python scripts/unbalanced_partial_smoke.py --case all --include-optional-uot-1d --json`; a missing optional backend appears as a structured skip. |
| `uot_1d` returns marginals rather than a plan | This is its API: it returns reweighted marginals and a loss. | If a full matrix plan is needed, use matrix solvers on `M = ot.dist(x[:, None], y[:, None])`. | Validate `u_reweighted.sum()` and `v_reweighted.sum()`, not `G.shape`. |
| `barycenter_unbalanced` output mass differs from inputs | Unbalanced barycenter optimizes mass under marginal relaxation. | Treat mass as an output. Increase `reg_m` to penalize mass change more strongly. | Check `bary.shape`, finite nonnegative values, and total mass trend as `reg_m` changes. |
| `regularization_path` is slow or memory-heavy | Path methods operate on flattened `len(a) * len(b)` plans and can be expensive. | Use smaller supports for diagnosis; reduce `itmax`; sample selected `gamma` values rather than plotting full paths. | `compute_transport_plan(...).reshape(M.shape)` is finite. |
| Gromov partial/unbalanced route is confusing | Linear OT and GW use different structure inputs and solver names. | Use this sub-skill only to settle mass semantics (`m`, `reg_marginals`, `epsilon`, `divergence`). Route graph/structure modeling to `gromov`. | GW plan has shape `(len(p), len(q))` and is validated by GW-specific checks. |

## Input validation helper

Add a pre-solve check like this to user workflows:

```python
import numpy as np

def validate_weights_and_cost(a, b, M, *, m=None):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    M = np.asarray(M, dtype=float)
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("a and b must be one-dimensional histograms")
    if M.shape != (a.size, b.size):
        raise ValueError(f"M has shape {M.shape}, expected {(a.size, b.size)}")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or not np.isfinite(M).all():
        raise ValueError("weights and cost matrix must be finite")
    if (a < 0).any() or (b < 0).any():
        raise ValueError("weights must be nonnegative")
    if m is not None and not (0 <= m <= min(a.sum(), b.sum())):
        raise ValueError("partial mass m must be between 0 and min(a.sum(), b.sum())")
    return a, b, M
```

## Parameter tuning patterns

### Tuning partial mass `m`

- If `a` and `b` are probability histograms, `m=0.8` means 80% of total mass.
- If `a.sum()` and `b.sum()` are not one, `m=0.8` means absolute mass `0.8`, not 80%; use `m=0.8 * min(a.sum(), b.sum())` for 80%.
- For outliers, start from the estimated clean shared mass and inspect which atoms are left unused.

### Tuning UOT `reg_m`

- Use larger `reg_m` when marginal fidelity matters more than ignoring outliers.
- Use smaller `reg_m` when outlier deletion/creation is desirable.
- For asymmetric trust, use a pair such as `(source_penalty, target_penalty)` in APIs that support paired relaxation.
- Re-tune after any cost rescaling.

### Tuning entropic `reg`

- Larger `reg` gives smoother, more diffuse plans and better numerical behavior.
- Smaller `reg` approaches sharper/exact-like plans but can underflow in multiplicative-domain methods.
- For entropic partial OT at small `reg`, switch to `method="sinkhorn_log"` before treating NaNs as a data issue.

## Exact versus entropic partial solvers

Choose exact `partial_wasserstein` when:

- You need an exact sparse plan or cost on a modest dense problem.
- Differentiability/smoothness is not required.
- You can handle potential EMD dummy-point tuning with `nb_dummies`.

Choose entropic `entropic_partial_wasserstein` when:

- You want a smoother plan or a Sinkhorn-like workflow.
- You can choose a positive `reg` and tolerate approximate mass within numerical tolerance.
- You are prepared to use `method="sinkhorn_log"` for small `reg` or large cost scales.

## Optional backend notes

- The minimum verified environment for this skill covered NumPy POT behavior only.
- `ot.unbalanced.uot_1d` requires PyTorch or JAX arrays; its behavior is optional unless that backend is installed and separately verified.
- `lbfgsb_unbalanced` converts through NumPy for SciPy optimization, so backend arrays can incur copy overhead.
- Plotting examples require plotting extras; the bundled runtime smoke helper deliberately avoids plotting.
