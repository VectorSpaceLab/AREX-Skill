# POT domain-adaptation workflows

Use these recipes after selecting an OTDA estimator from the API reference. They use synthetic arrays or user-provided arrays only; they do not depend on any original repository examples or data files.

## 1. Baseline 2D adaptation with EMD or Sinkhorn

Use this route when source and target samples share feature dimension and the task is to map source samples into the target geometry.

```python
import numpy as np
import ot

Xs = np.array([[-1.0, 0.0], [-1.0, 1.0], [0.0, -1.0], [0.0, 0.0]])
Xt = Xs + np.array([2.0, 0.5])

emd = ot.da.EMDTransport(metric="sqeuclidean", out_of_sample_map="ferradans")
emd.fit(Xs=Xs, Xt=Xt)
Xs_emd = emd.transform(Xs=Xs)
assert emd.coupling_.shape == (len(Xs), len(Xt))
assert Xs_emd.shape == Xs.shape

sinkhorn = ot.da.SinkhornTransport(reg_e=0.5, method="sinkhorn_log", max_iter=500)
sinkhorn.fit(Xs=Xs, Xt=Xt)
Xs_s = sinkhorn.transform(Xs=Xs)
assert np.isfinite(sinkhorn.coupling_).all()
```

Decision points:

- Choose `EMDTransport` for an exact, sparse baseline on small data.
- Choose `SinkhornTransport` for smoother couplings, differentiability-friendly behavior, or larger dense problems.
- Inspect `cost_` before fitting if feature scales differ. Use `norm="median"`, `"max"`, or explicit preprocessing when one feature dominates.
- Validate both the coupling and transformed samples. A numerically finite coupling does not guarantee that the mapped samples answer the modeling question.

## 2. Class-regularized and semi-supervised adaptation

Use source labels to penalize class-inconsistent transport. Use target labels only when they are known; set unknown target labels to `-1`.

```python
ys = np.array([0, 0, 1, 1])
yt_partial = np.array([0, -1, 1, -1])

semi = ot.da.SinkhornTransport(reg_e=0.5, method="sinkhorn_log")
semi.fit(Xs=Xs, ys=ys, Xt=Xt, yt=yt_partial)
assert semi.coupling_.shape == (4, 4)

class_reg = ot.da.SinkhornLpl1Transport(reg_e=0.5, reg_cl=0.1, max_iter=5)
class_reg.fit(Xs=Xs, ys=ys, Xt=Xt)
assert class_reg.coupling_.shape == (4, 4)
```

Guidance:

- `SinkhornLpl1Transport` and `SinkhornL1l2Transport` need `ys`; without labels they cannot build class groups.
- Unknown target labels must be `-1`. If `-1` is a real class label, remap labels before calling POT.
- For semi-supervised target labels, POT modifies the cost matrix so source samples are discouraged or prevented from matching incompatible known target classes.

## 3. Learned mappings for out-of-sample source points

`transform` on the original fitted `Xs` can use barycentric mapping from the coupling. For new source points, use a learned mapping estimator.

```python
mapper = ot.da.MappingTransport(
    kernel="linear",
    mu=1.0,
    eta=1e-3,
    bias=True,
    max_iter=10,
    max_inner_iter=10,
)
mapper.fit(Xs=Xs, Xt=Xt)
Xs_new = Xs + np.array([0.2, -0.1])
Xs_new_mapped = mapper.transform(Xs_new)
assert Xs_new_mapped.shape == Xs_new.shape
```

Choose `kernel="linear"` for affine shifts and `kernel="gaussian"` for nonlinear deformations. Increase `max_iter` and `max_inner_iter` only after a tiny fixture works, because mapping estimation alternates an OT coupling with a mapping optimization.

For a direct linear map without estimator wrapper, use `ot.mapping.joint_OT_mapping_linear(xs, xt, ...)`; it returns mapping parameters and logs rather than a full `ot.da` estimator interface.

## 4. Multi-source target-shift adaptation with JCPOT

Use `JCPOTTransport` when there are several labeled source domains and an unlabeled target domain whose class proportions may differ.

```python
Xs_list = [Xs, Xs + np.array([0.5, -0.25])]
ys_list = [ys, ys]

jcpot = ot.da.JCPOTTransport(reg_e=0.5, max_iter=20, tol=1e-7)
jcpot.fit(Xs=Xs_list, ys=ys_list, Xt=Xt)
assert isinstance(jcpot.coupling_, list)
assert len(jcpot.coupling_) == len(Xs_list)
proportions = np.asarray(jcpot.proportions_[0] if isinstance(jcpot.proportions_, tuple) else jcpot.proportions_)
assert np.isfinite(proportions).all()
```

Checklist:

- `Xs` and `ys` must both be lists of the same length.
- Each `ys[k]` length must match `Xs[k].shape[0]`.
- Source label sets should be compatible across sources.
- Validate `proportions_`; target-shift estimates should be finite and nonnegative.

## 5. Image or color transfer without source data dependency

POT image/color examples flatten pixel arrays into samples, fit a transport or mapping from source colors to target colors, then reshape mapped colors back to image layout. Use user-provided arrays, not bundled source images.

```python
# source_rgb and target_rgb are user-provided arrays with shape (height, width, 3)
source_pixels = source_rgb.reshape(-1, 3).astype(float) / 255.0
target_pixels = target_rgb.reshape(-1, 3).astype(float) / 255.0

# Downsample or cluster pixels before fitting on large images.
transport = ot.da.SinkhornTransport(reg_e=0.05, method="sinkhorn_log", max_iter=500)
transport.fit(Xs=source_pixels, Xt=target_pixels)
recolored = transport.transform(Xs=source_pixels).reshape(source_rgb.shape)
recolored = np.clip(recolored, 0.0, 1.0)
```

Avoid fitting a dense coupling on every pixel of a large image. Subsample, cluster colors, or use a mapping estimator when the pixel count is large.

## 6. Optional WDA/EWCA and dimensionality reduction

`ot.dr` is not imported by default and requires optional dependencies. Verify first:

```python
try:
    import ot.dr
except ImportError as exc:
    raise RuntimeError("Install POT[dr] or autograd, pymanopt, and scikit-learn before WDA/EWCA") from exc
```

Use WDA/EWCA when the task is a projection or dimensionality-reduction objective, not a direct sample-to-sample mapping. Keep it separate from `ot.da.MappingTransport` unless the user explicitly wants both a projection and a transport map.

## 7. Optional nearest Brenier potential

Nearest Brenier potential workflows rely on a convex optimization problem and need `cvxpy` at call time.

```python
try:
    import cvxpy  # noqa: F401
except ImportError as exc:
    raise RuntimeError("Install cvxpy before using nearest Brenier potential workflows") from exc

nbp = ot.da.NearestBrenierPotential(its=10, seed=0)
# Fit only after verifying small data, because the QCQP can be expensive.
```

Start with very small fixtures and explicit solver settings. If the convex solver fails, simplify the partition/classes, reduce sample count, or use ordinary linear/mapping transport instead.

## 8. Use the bundled smoke helper

Run the helper from this sub-skill directory or pass its path explicitly:

```bash
python scripts/domain_adaptation_smoke.py --case all --json
python scripts/domain_adaptation_smoke.py --case dependencies --json
```

Expected results in a NumPy-only environment:

- `emd` and `sinkhorn` should pass.
- `mapping` and `jcpot` should pass on tiny fixtures in a standard POT install; if the environment lacks a required solver behavior, the helper reports a structured skip/failure with a reason.
- `dependencies` reports optional dependency import status; missing optional packages do not fail the NumPy OTDA smoke.
