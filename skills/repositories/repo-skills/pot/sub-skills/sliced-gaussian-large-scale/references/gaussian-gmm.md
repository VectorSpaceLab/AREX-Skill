# Gaussian and GMM OT workflows

Use this reference when distributions are already represented as Gaussian or Gaussian-mixture parameters. The key advantage is avoiding a potentially expensive discretization into many samples.

## Choose the parameterized route

| User input | Use | Why |
| --- | --- | --- |
| One Gaussian source and one Gaussian target | `ot.gaussian.bures_wasserstein_distance` or `bures_wasserstein_mapping` | Closed-form W2/Bures computation and affine map. |
| Many Gaussian components with weights | `ot.gmm.gmm_ot_plan`, `gmm_ot_loss`, `gmm_ot_apply_map` | Component-level OT plan using Gaussian costs. |
| Sample clouds assumed Gaussian | `ot.gaussian.empirical_bures_wasserstein_distance` or mapping | Estimate means/covariances from samples; avoid arbitrary histogram grids. |
| High-dimensional low-rank covariance model | `bures_wasserstein_distance_hd` or `mapping_hd` | Use `U diag(l) U.T + sigma2 I` representation. |
| Family-level barycenter | `bures_wasserstein_barycenter` or `gmm_barycenter_fixed_point` | Keep the result in the Gaussian/GMM family. |

## Validate Gaussian parameters

Before calling Gaussian APIs:

```python
import numpy as np

def symmetrize_psd(C, jitter=0.0):
    C = 0.5 * (C + C.T)
    if jitter:
        C = C + jitter * np.eye(C.shape[0])
    vals = np.linalg.eigvalsh(C)
    if np.min(vals) < -1e-8:
        raise ValueError(f"covariance is not PSD; min eigenvalue={np.min(vals):.3e}")
    return C
```

Use a small jitter such as `1e-8` only when the negative eigenvalue is numerical noise and record it as a repair. Do not hide truly indefinite covariance estimates.

## Gaussian Bures distance and affine map

```python
import numpy as np
import ot

ms = np.array([0.0, 0.0])
mt = np.array([1.0, -2.0])
Cs = np.array([[1.0, 0.2], [0.2, 0.8]])
Ct = np.array([[1.5, 0.1], [0.1, 0.6]])

W = ot.gaussian.bures_wasserstein_distance(ms, mt, Cs, Ct)
A, b = ot.gaussian.bures_wasserstein_mapping(ms, mt, Cs, Ct)

x = np.array([[0.0, 0.0], [1.0, 0.5]])
x_mapped = x @ A + b
assert x_mapped.shape == x.shape
print(float(W), x_mapped[:2])
```

Validation checks:

- If `Cs == Ct`, the distance should reduce to the Euclidean distance between means.
- The map should send the source mean close to the target mean: `ms @ A + b ~= mt` for row-wise samples.
- For batched cross-distances, check the output shape: `(n_source_gaussians, n_target_gaussians)`. Use `paired=True` only for one-to-one pairs.

## Empirical Gaussian route from samples

When samples are believed Gaussian, avoid constructing a dense sample OT plan unless the task specifically needs one:

```python
import numpy as np
import ot

rng = np.random.RandomState(0)
X_s = rng.normal(size=(100, 3))
X_t = rng.normal(loc=0.5, size=(120, 3))

W = ot.gaussian.empirical_bures_wasserstein_distance(X_s, X_t, reg=1e-6, bias=True)
A, b = ot.gaussian.empirical_bures_wasserstein_mapping(X_s, X_t, reg=1e-6, bias=True)
print(float(W), A.shape, b.shape)
```

If covariance estimation is unstable, increase `reg` modestly and check whether the affine map has finite entries.

## High-dimensional Gaussian representation

High-dimensional helpers use a covariance model of the form:

```text
Cov = U @ diag(l) @ U.T + sigma2 * I
```

Use them when the ambient dimension is large but the principal subspace dimension is modest. Required inputs:

- `ms`, `mt`: means `(p,)`.
- `Us`, `Ut`: orthogonal bases `(p, ds)` and `(p, dt)`.
- `ls`, `lt`: principal variances `(ds,)` and `(dt,)`.
- `sigma2_s`, `sigma2_t`: residual variances.

Validation checks:

1. `U.T @ U` should be close to identity for each subspace basis.
2. Principal and residual variances should be nonnegative.
3. On a tiny version, compare the high-dimensional helper with the full covariance API.

## Gaussian barycenter

```python
import numpy as np
import ot

m = np.array([[0.0, 0.0], [2.0, 0.0], [0.0, 2.0]])
C = np.stack([np.eye(2), 2.0 * np.eye(2), np.diag([1.0, 3.0])])
weights = np.array([0.2, 0.5, 0.3])

mb, Cb = ot.gaussian.bures_wasserstein_barycenter(
    m, C, weights=weights, method="fixed_point", num_iter=200, eps=1e-7
)
assert mb.shape == (2,)
assert Cb.shape == (2, 2)
print(mb, Cb)
```

Use `method="gradient_descent"` or stochastic variants only after validating convergence and step-size behavior on a tiny case.

## GMM component plan and map

```python
import numpy as np
import ot

m_s = np.array([[0.0], [2.0]])
m_t = np.array([[1.0], [3.0], [4.0]])
C_s = np.array([[[0.2]], [[0.3]]])
C_t = np.array([[[0.2]], [[0.25]], [[0.4]]])
w_s = np.array([0.4, 0.6])
w_t = np.array([0.3, 0.3, 0.4])

plan = ot.gmm.gmm_ot_plan(m_s, m_t, C_s, C_t, w_s, w_t)
loss = ot.gmm.gmm_ot_loss(m_s, m_t, C_s, C_t, w_s, w_t)
assert np.allclose(plan.sum(axis=1), w_s)
assert np.allclose(plan.sum(axis=0), w_t)

x = np.linspace(-1.0, 3.0, 8)[:, None]
y_bary = ot.gmm.gmm_ot_apply_map(x, m_s, m_t, C_s, C_t, w_s, w_t, plan=plan, method="bary")
y_rand = ot.gmm.gmm_ot_apply_map(x, m_s, m_t, C_s, C_t, w_s, w_t, plan=plan, method="rand", seed=0)
print(float(loss), y_bary.shape, y_rand.shape)
```

Map method choice:

- `method="bary"`: deterministic barycentric map; best default for reproducible workflows.
- `method="rand"`: random component-pair map; pass `seed` and treat outputs as stochastic.

## GMM density and barycenter

Use `ot.gmm.gmm_ot_plan_density` only when the caller needs an evaluation-grid density of the GMM-OT plan. It can allocate an `(n_x, n_y)` matrix, so use a coarse grid first.

For GMM barycenters:

```python
means_list = [m_s, m_t[:2]]
covs_list = [C_s, C_t[:2]]
w_list = [w_s, np.array([0.5, 0.5])]
means_init = m_s.copy()
covs_init = C_s.copy()
weights = np.array([0.5, 0.5])
means, covs = ot.gmm.gmm_barycenter_fixed_point(
    means_list, covs_list, w_list, means_init, covs_init, weights,
    iterations=5, barycentric_proj_method="euclidean"
)
```

Use `barycentric_proj_method="euclidean"` as the fast default. `"bures"` is more faithful to Gaussian geometry but slower.

## Validation checklist for Gaussian/GMM workflows

- Covariance arrays are symmetric PSD and have shape `(d, d)` or `(k, d, d)`.
- Means have matching dimension `d`.
- GMM weights match component counts and sum to one.
- Component plan row sums equal source weights and column sums equal target weights.
- Mapping output shape matches input sample shape.
- For random GMM maps, pass a seed and report stochasticity.
- Optional differentiable backend or gradient-flow workflows are not guaranteed in the NumPy-only baseline; route backend questions to `backend-and-batch`.
