---
name: metrics-backends
description: "Guides tslearn metric, backend, autodiff, performance-metric, and
  barycenter workflows for time-series distance tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Metrics and Backends

Use this sub-skill when a task needs tslearn distance, similarity, alignment,
backend, differentiable-loss, forecasting-error, or barycenter guidance. It is
self-contained for the metric APIs; return to the [root tslearn router](../../SKILL.md)
when the task is really about an estimator, data preparation, forecasting,
serialization, or another repo workflow.

## Read this when

- You need DTW, Soft-DTW, GAK, LCSS, Fréchet, CTW, pairwise/cross-distance
  matrices, path extraction, masks, or numeric warping constraints.
- You need to decide whether plain NumPy is enough or a PyTorch backend is
  required for tensors, gradients, or `SoftDTWLossPyTorch`.
- You need `tslearn.metrics.performance` (`mae`, `mse`, `mase`) or
  `tslearn.barycenters` (`euclidean_barycenter`, DBA, Soft-DTW barycenters).
- You need a tiny numeric smoke helper instead of plotting gallery examples.

## Scope boundaries

Covered here:

- `tslearn.metrics`, including path helpers, cross-distance helpers, masks,
  Soft-DTW classes, GAK bandwidth helpers, LCSS, Fréchet, and CTW.
- `tslearn.backend`, `Backend`, `NumPyBackend`, `PyTorchBackend`, `cast`,
  `instantiate_backend`, and backend-selection pitfalls.
- `tslearn.metrics.performance` and `tslearn.barycenters`.
- Optional PyTorch autograd and the PyTorch-only `SoftDTWLossPyTorch` module.

Do not use this sub-skill as the owner for:

- Clustering estimators that merely consume metric strings or `metric_params`:
  route fitting, labels, centroids, and model selection to
  [clustering](../clustering/SKILL.md); only return here for the metric-specific
  parameter semantics.
- Supervised estimators and GAK SVM/SVR model workflows: route to
  [supervised-models](../supervised-models/SKILL.md) and return here only for
  reusable metric/backend details.
- Forecasting model classes: route to [forecasting](../forecasting/SKILL.md);
  this sub-skill owns only `tslearn.metrics.performance` scoring.
- Serialization, matrix profile, HDF5, JSON/Pickle round-trips, and persistence:
  route to [analysis-and-persistence](../analysis-and-persistence/SKILL.md).
- Data-preparation utilities, scaling, resampling, or dataset loading: return to
  the [root router](../../SKILL.md) unless a sibling data-preparation route is
  available in the final integrated skill tree.

## Fast decision checklist

1. **Default to NumPy for correctness.** Lists and NumPy arrays with `be=None`
   select the NumPy backend and cover ordinary distance matrices, paths,
   performance metrics, and barycenters.
2. **Use PyTorch only when the task asks for tensors or gradients.** Pass
   torch tensors (auto-detected) or `be="pytorch"`; use
   `SoftDTWLossPyTorch` for batched training losses.
3. **Do not require CUDA for this sub-skill.** CUDA availability can help only
   if the actual torch operations run on CUDA tensors; CPU correctness is the
   portable baseline and `SoftDTWLossPyTorch` still has CPU-side dynamic
   programming work.
4. **Validate shapes before blaming the metric.** A single series is `(sz, d)`
   or `(sz,)`; datasets are `(n_ts, sz, d)` or compatible lists. Pairwise
   metrics require non-empty series and matching feature dimensions.
5. **Name constraints explicitly.** Use `global_constraint="sakoe_chiba"` with
   `sakoe_chiba_radius`, or `global_constraint="itakura"` with
   `itakura_max_slope`; mixed constraint parameters without a global constraint
   are a common warning source.

## Runtime references

- [API reference](references/api-reference.md): metric families, signatures,
  return values, path helpers, constraints, Soft-DTW classes, and barycenters.
- [Backends and autodiff](references/backends.md): backend selection rules,
  NumPy-vs-PyTorch choices, backend classes, and gradient caveats.
- [Performance metrics](references/performance.md): MAE, MSE, MASE shapes,
  weighting, aggregation, and scaled-error caveats.
- [Troubleshooting](references/troubleshooting.md): missing torch, backend
  strings, empty inputs, impossible constraints, gradients, CUDA expectations,
  GAK sigma, and MASE divide-by-zero.

## Bundled helper

Run or adapt [scripts/metrics_smoke.py](scripts/metrics_smoke.py) when you need
safe numeric confirmation. It distills the assigned plotting/autodiff examples
into deterministic, no-download subcommands. From the generated `tslearn/`
skill root, run:

```bash
python sub-skills/metrics-backends/scripts/metrics_smoke.py --help
python sub-skills/metrics-backends/scripts/metrics_smoke.py all
python sub-skills/metrics-backends/scripts/metrics_smoke.py dtw --backend numpy
python sub-skills/metrics-backends/scripts/metrics_smoke.py softdtw-loss
```

The helper is intentionally tiny: it checks representative values and exits
non-zero on real failures, but it is not a benchmark and does not prove CUDA
acceleration.

## Minimal workflow patterns

### Pairwise or path metric

1. Convert series to numeric arrays/tensors with consistent feature dimensions.
2. Choose the family: `dtw`, `soft_dtw`, `gak`, `lcss`, `frechet`, or `ctw`.
3. Use the scalar function for one pair, the `*_path` helper when alignment
   indices matter, and `cdist_*` for cross-similarity matrices.
4. If you use a custom ground metric, prefer `dtw_path_from_metric`,
   `lcss_path_from_metric`, or `frechet_path_from_metric`, then validate whether
   the returned score is a cumulative squared/custom cost rather than a plain
   Euclidean distance.

### Differentiable metric or loss

1. Use torch tensors with `requires_grad=True` for the tensor being optimized.
2. Select `be="pytorch"` or rely on tensor auto-detection; verify the selected
   backend from [backends](references/backends.md) if behavior is surprising.
3. Prefer `soft_dtw` or `SoftDTWLossPyTorch` for training-like workflows;
   aggregate the per-example loss before `backward()`.
4. Keep custom `dist_func` implementations in torch, returning a
   `(batch, m, n)` distance tensor.

### Barycenter computation

1. Use `euclidean_barycenter` only when an arithmetic mean under aligned time
   axes is intended.
2. Use `dtw_barycenter_averaging`/DBA when alignment under DTW matters; pass
   DTW constraints through `metric_params`.
3. Use `softdtw_barycenter` when the smoothing parameter `gamma` is part of the
   model choice; set `init` or `barycenter_size`/initialization choices
   deliberately when target length matters.
4. Treat barycenters as CPU-sufficient unless a separate, verified backend plan
   requires otherwise.
