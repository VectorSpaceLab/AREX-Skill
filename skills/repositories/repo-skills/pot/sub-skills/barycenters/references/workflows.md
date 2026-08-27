# Barycenter workflows

Use this reference when translating a user request into the smallest adequate POT barycenter workflow. The examples here are self-contained package-level recipes; they do not depend on external example files.

## 1. Choose the barycenter family

| User data / goal | Use this API first | Why | Route away when |
| --- | --- | --- | --- |
| Histograms already share one support grid | `ot.bregman.barycenter` or `ot.lp.barycenter` | Learns only barycenter weights on that fixed grid. | The support points themselves should move. |
| Fixed grid but entropic blur is too high | `ot.bregman.barycenter_debiased` | Debiased Sinkhorn-divergence objective reduces regularization bias. | The task is exact small LP validation; use `ot.lp.barycenter`. |
| Discrete point-cloud measures and chosen barycenter support size | `ot.lp.free_support_barycenter` | Exact 2-Wasserstein free-support fixed-point update. | Exact inner EMD is too slow or noisy; use Sinkhorn free support. |
| Same as above, but regularized inner plans are acceptable | `ot.bregman.free_support_sinkhorn_barycenter` | Entropic inner Sinkhorn plans can be faster/smoother. | `reg` must be extremely small and convergence is unstable. |
| Unequal sample clouds, support to be learned, regularized/unbalanced variants needed | `ot.solvers.solve_bary_sample` | Wraps BCD over inner `ot.solve_sample` problems and returns `BaryResult`. | Inputs are already histograms on a shared grid; use fixed-support APIs. |
| Stacked images on a regular 2D grid | `ot.bregman.convolutional_barycenter2d` or `_debiased` | Uses separable convolutional Sinkhorn operators for images. | Images are not aligned to a common grid or are graph/mesh structures. |
| Gaussian means/covariances or GMM components | `ot.gaussian.*` or `ot.gmm.*` barycenter APIs | Avoids discretizing parametric distributions. | Route detailed setup to `sliced-gaussian-large-scale`. |
| Graphs, shortest-path matrices, labels, or structured supports | GW/FGW barycenter APIs | These are Gromov-Wasserstein objects, not ordinary Wasserstein histograms. | Route detailed setup to `gromov`. |

## 2. Prepare fixed-support histograms

1. Put histograms in columns:

   ```python
   # hists has shape (n_hists, n_bins); POT fixed-support barycenters need columns.
   A = hists.T
   A = A / A.sum(axis=0, keepdims=True)
   ```

2. Build a square finite nonnegative cost matrix on the shared support:

   ```python
   x = support_coordinates.reshape(-1, 1)
   M = ot.dist(x, x)
   if M.max() > 0:
       M = M / M.max()
   ```

3. Start with entropic Sinkhorn for moderate grids:

   ```python
   weights = np.array([0.25, 0.25, 0.50])
   bary = ot.bregman.barycenter(A, M, reg=1e-2, weights=weights)
   assert bary.shape == (A.shape[0],)
   assert np.allclose(bary.sum(), 1.0, atol=1e-6)
   ```

4. For tiny exact checks, compare against the LP barycenter:

   ```python
   bary_exact = ot.lp.barycenter(A, M, weights=weights, solver='highs-ipm')
   ```

5. If the entropic result is too diffuse at usable `reg`, switch to the debiased objective:

   ```python
   bary_debiased = ot.bregman.barycenter_debiased(A, M, reg=1e-2, weights=weights)
   ```

Validation command:

```bash
python scripts/barycenter_smoke.py --case fixed-support
```

## 3. Prepare free-support point-cloud barycenters

Use this path when the input measures are lists of atoms and you choose the barycenter atom count `k`.

```python
measures_locations = [X1, X2, X3]       # each X_i has shape (n_i, d)
measures_weights = [ot.unif(len(X)) for X in measures_locations]
X_init = initial_support                 # shape (k, d)
b = ot.unif(k)                           # barycenter weights, fixed by the solver
weights = ot.unif(len(measures_locations))

X_exact = ot.lp.free_support_barycenter(
    measures_locations,
    measures_weights,
    X_init,
    b=b,
    weights=weights,
    numItermax=100,
    stopThr=1e-7,
)

X_sinkhorn = ot.bregman.free_support_sinkhorn_barycenter(
    measures_locations,
    measures_weights,
    X_init,
    reg=0.1,
    b=b,
    weights=weights,
    numItermax=100,
    numInnerItermax=1000,
    stopThr=1e-7,
)
```

Practical setup rules:

- `X_init.shape[1]` must match the source dimension `d`.
- `b.shape[0]` must match `X_init.shape[0]`.
- `measures_weights[i].shape[0]` must match `measures_locations[i].shape[0]`.
- The `weights` vector weights entire input measures; it is not the same as each measure's sample weights.
- Initialize near the data scale. Very far initial supports may need more iterations and can conceal convergence problems.

Validation command:

```bash
python scripts/barycenter_smoke.py --case free-support
```

## 4. Use `solve_bary_sample` for unequal sample clouds

Choose this over fixed-grid barycenters when source clouds have different sizes or when no common histogram grid exists.

```python
X_a_list = [X1, X2, X3]                  # shapes (n_i, d), n_i may differ
a_list = [ot.unif(X.shape[0]) for X in X_a_list]
w = ot.unif(len(X_a_list))
n_bary = 20
X_b_init = np.vstack([X[:n_bary] for X in X_a_list if X.shape[0] >= n_bary])[:n_bary]

res = ot.solvers.solve_bary_sample(
    X_a_list,
    n=n_bary,
    a_list=a_list,
    w=w,
    X_b_init=X_b_init,
    metric='sqeuclidean',
    reg=None,
    stopping_criterion='loss',
    max_iter_bary=100,
    tol_bary=1e-5,
)

assert res.X.shape == (n_bary, X_a_list[0].shape[1])
assert np.allclose(res.b.sum(), 1.0, atol=1e-6)
assert len(res.list_res) == len(X_a_list)
```

Turn on inner regularization only when needed:

```python
res_reg = ot.solvers.solve_bary_sample(
    X_a_list,
    n=n_bary,
    a_list=a_list,
    w=w,
    X_b_init=res.X,
    metric='sqeuclidean',
    reg=0.1,
    reg_type='KL',
    warmstart=True,
    max_iter_bary=100,
)
```

Unbalanced sample-cloud barycenters use the same interface but set `unbalanced` and optionally `unbalanced_type`:

```python
res_uot = ot.solvers.solve_bary_sample(
    X_a_list,
    n=n_bary,
    a_list=a_list,
    w=w,
    X_b_init=res.X,
    metric='sqeuclidean',
    reg=0.1,
    unbalanced=1.0,
    unbalanced_type='KL',
)
```

Validation command:

```bash
python scripts/barycenter_smoke.py --case sample-cloud
```

## 5. Use convolutional image barycenters

1. Stack images on axis 0 and normalize each image independently.

   ```python
   A = np.asarray([img1, img2, img3], dtype=float)
   A = np.maximum(A, 0)
   A = A / A.sum(axis=(1, 2), keepdims=True)
   weights = ot.unif(A.shape[0])
   ```

2. Start with ordinary convolutional Sinkhorn.

   ```python
   bar = ot.bregman.convolutional_barycenter2d(
       A,
       reg=1e-2,
       weights=weights,
       method='sinkhorn',
       numItermax=10000,
   )
   assert bar.shape == A.shape[1:]
   assert np.allclose(bar.sum(), 1.0, atol=1e-3)
   ```

3. If the output is over-smoothed, try debiased convolutional barycenters.

   ```python
   bar_debiased = ot.bregman.convolutional_barycenter2d_debiased(
       A,
       reg=1e-2,
       weights=weights,
       method='sinkhorn',
   )
   ```

Validation command:

```bash
python scripts/barycenter_smoke.py --case convolutional
```

## 6. Validate before larger runs

Run the full bundled smoke suite first:

```bash
python scripts/barycenter_smoke.py --case all
```

Then validate the task-specific invariants:

- Fixed-support barycenter sums to one and has shape `(n_bins,)`.
- Free-support barycenter has shape `(k, d)` and remains finite.
- `solve_bary_sample` returns a `BaryResult` with finite `value`, `res.X.shape == (n, d)`, and one inner result per source distribution.
- Convolutional image barycenter has shape `(height, width)` and finite nonnegative mass.
- If the problem is Gaussian/GMM/GW/FGW, stop and route to the owning sub-skill instead of forcing a histogram barycenter.

## 7. Recovery defaults

When a barycenter run fails or becomes numerically suspicious, try these changes in order:

1. Re-check shapes and simplex normalization before changing solvers.
2. Normalize the cost scale: `M = M / M.max()` for nonzero `M`.
3. Increase `reg` by 2x-10x for Sinkhorn-family methods.
4. Increase `numItermax`; for free-support Sinkhorn also increase `numInnerItermax`.
5. Use `method='sinkhorn_stabilized'` or `method='sinkhorn_log'` for fixed-support entropic barycenters when available.
6. Use debiased barycenters when ordinary entropic barycenters are stable but too diffuse.
7. For large fixed-support LP problems, switch to entropic or sample-cloud/free-support formulations; the LP problem is not intended to scale.
