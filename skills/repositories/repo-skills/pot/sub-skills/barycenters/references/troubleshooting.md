# Barycenter troubleshooting

Use this reference when a POT barycenter workflow raises a shape error, returns surprising mass, does not converge, or appears to choose the wrong solver family.

## Fast diagnostic checklist

Run the relevant deterministic check before debugging a larger task:

```bash
python scripts/barycenter_smoke.py --case fixed-support
python scripts/barycenter_smoke.py --case free-support
python scripts/barycenter_smoke.py --case sample-cloud
python scripts/barycenter_smoke.py --case convolutional
```

If those pass, the local POT install is adequate for the NumPy barycenter workflows covered here; focus on the task data and parameters.

## Common failure modes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `assert len(weights) == A.shape[1]` or the barycenter is clearly using the wrong distributions | Histograms were passed as rows instead of columns, or the barycentric `weights` vector has the wrong length. | For fixed-support APIs, pass `A.shape == (n_bins, n_hists)`. If your array is `(n_hists, n_bins)`, call `A = A.T`. Use `weights.shape == (n_hists,)`. |
| Barycenter mass is not close to one | Input histograms or image slices were not normalized, or negative values were present. | Clip only if appropriate for the data, then normalize: `A = np.maximum(A, 0); A /= A.sum(axis=0, keepdims=True)` for fixed-support histograms, or `A /= A.sum(axis=(1, 2), keepdims=True)` for image stacks. Check zero columns/images before dividing. |
| Fixed-support call fails or returns nonsensical values with a cost matrix | `M` is non-square, has NaN/Inf entries, has negative costs, or does not correspond to the histogram support. | Rebuild `M` from support coordinates with `ot.dist(x, x)`. Ensure `M.shape == (A.shape[0], A.shape[0])`, `np.isfinite(M).all()`, and `M.min() >= 0`. Normalize nonzero costs by `M.max()` before choosing `reg`. |
| `Sinkhorn did not converge` or `Convolutional Sinkhorn did not converge` | `reg` is too small for the cost scale, iteration limits are too low, or the problem has near-zero/ill-scaled masses. | First normalize `M` or image masses. Increase `reg`; increase `numItermax`; for `free_support_sinkhorn_barycenter`, also increase `numInnerItermax`. For fixed-support `ot.bregman.barycenter`, try `method='sinkhorn_stabilized'` or `method='sinkhorn_log'`. |
| Tiny `reg` gives mass or shape surprises even after convergence | Entropic regularization can bias or blur the barycenter; very small `reg` can also make Sinkhorn numerically fragile. | Compare against `ot.lp.barycenter` on a tiny downsampled fixture. If the issue is blur rather than instability, try `ot.bregman.barycenter_debiased` or `ot.bregman.convolutional_barycenter2d_debiased`. |
| `ot.lp.barycenter` is very slow or memory-heavy | Exact fixed-support barycenter is a large linear program. | Use LP only for small grids or sanity checks. Prefer `ot.bregman.barycenter` for moderate grids, convolutional barycenters for images, or free-support/sample-cloud formulations when the support can move. |
| Solver argument mentions `cvxopt`, `glpk`, or `mosek` but import fails | Optional LP solver dependencies are not installed. | Use the default `solver='highs-ipm'` SciPy path unless a specific external LP solver is required. Treat `cvxopt` and external commercial solvers as optional/unverified. |
| Free-support barycenter stays near `X_init` or oscillates | Initial support is far from source clouds, barycenter atom count is poorly chosen, or stop tolerance is too strict/loose for the data scale. | Initialize `X_init` from pooled samples or a coarse k-means-like subset. Match `X_init.shape == (k, d)` and `b.shape == (k,)`. Increase `numItermax`; for Sinkhorn free support increase `reg` and `numInnerItermax`. Inspect `log['displacement_square_norms']` when `log=True`. |
| `measures_weights` or `weights` confusion in free support | Per-measure sample weights and barycentric coefficients were swapped. | `measures_weights[i]` weights atoms inside `measures_locations[i]`. `weights` weights whole input measures and has length `len(measures_locations)`. `b` weights the barycenter atoms and has length `X_init.shape[0]`. |
| `solve_bary_sample` raises `X_b_init must have shape (n, dim)` | The initialization has the wrong number of rows or feature dimension. | Pass `X_b_init.shape == (n, X_a_list[0].shape[1])`, or omit `X_b_init` and set `random_state` for deterministic initialization. |
| `solve_bary_sample` raises `stopping_criterion must be either 'loss' or 'bary'` | Invalid stopping criterion string. | Use `stopping_criterion='loss'` to monitor objective change or `'bary'` to monitor support displacement. |
| `solve_bary_sample` raises `Barycenter solver with lazy=True not implemented` | Lazy sample barycenter is not implemented in POT. | Use `lazy=False` and keep the fixture small enough, or reformulate through a large-scale/sliced solver route if memory is the blocker. |
| `solve_bary_sample` with a callable metric fails | Callable metrics are balanced-only; automatic generic-cost updates require a compatible backend, and `true_fixed_point` requires an explicit ground barycenter function. | Keep `reg=None` and `unbalanced=None` for callable metrics. In a NumPy-only environment, avoid callable metrics or provide a compatible `ground_bary` workflow with a verified PyTorch backend. Route large/custom-cost design to the owning large-scale or backend sub-skill. |
| `method='sinkhorn_log'` with convolutional or debiased barycenters raises `NotImplementedError` on JAX/TF arrays | The log-domain image barycenter implementations do not support JAX/TF mutable update semantics. | Use NumPy or Torch arrays for log-domain image barycenters, or switch to `method='sinkhorn'`. Optional backends were not verified by the minimum NumPy setup. |
| User asks for GW, FGW, graph, Gaussian, or GMM barycenters | Wrong sub-skill family. | Route graph/structured barycenters to `gromov`. Route Gaussian and GMM barycenters to `sliced-gaussian-large-scale`; use this sub-skill only for cross-linking and ordinary Wasserstein histogram/point-cloud barycenters. |

## Debugging recipes

### Histograms as columns vs rows

Use this quick check before calling `ot.bregman.barycenter` or `ot.lp.barycenter`:

```python
assert A.ndim == 2
assert M.shape == (A.shape[0], A.shape[0])
assert weights.shape == (A.shape[1],)
assert np.allclose(A.sum(axis=0), 1.0)
assert np.allclose(weights.sum(), 1.0)
```

If `weights.shape[0] == A.shape[0]` and `M.shape[0] == A.shape[1]`, the histogram matrix is probably transposed.

### Choosing `solve_bary_sample` vs fixed-grid barycenter

Use `solve_bary_sample` when:

- source clouds have different lengths, e.g. `(43, d)`, `(80, d)`, `(12, d)`;
- the output should be new support locations `res.X` rather than weights on a pre-existing grid;
- inner regularized or unbalanced sample OT variants are part of the task.

Use fixed-grid `ot.bregman.barycenter`/`ot.lp.barycenter` when:

- every input already lives on the same bins/pixels/support locations;
- the desired output is a probability vector on those same bins;
- you have a square ground-cost matrix on the shared support.

### Small regularization recovery

When `reg` is tiny and convergence or mass is suspicious:

1. Normalize cost scale first.
2. Run `python scripts/barycenter_smoke.py --case fixed-support` to ensure POT's tiny barycenter behavior is fine.
3. Try `reg *= 10` and compare the trend.
4. Switch to `method='sinkhorn_stabilized'` or `method='sinkhorn_log'` for fixed-support barycenters.
5. Use debiased barycenters when ordinary Sinkhorn is stable but too blurred.
6. For exact low-dimensional confirmation, run a downsampled `ot.lp.barycenter` check rather than forcing an unstable tiny-`reg` Sinkhorn solve.
