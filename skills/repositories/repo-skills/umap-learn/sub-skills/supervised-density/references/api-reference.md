# Target and densMAP API reference

This reference covers the `umap.UMAP` surfaces owned by the supervised-density
sub-skill. Use the core-embedding sub-skill for base estimator mechanics,
feature metrics, sparse/precomputed inputs, and generic transform guidance.

## Entry points

| Method | Use in this sub-skill | Important behavior |
| --- | --- | --- |
| `fit(X, y=None, ensure_all_finite=True, **kwargs)` | Pass `y` for supervised or semi-supervised fitting. | `y` must have the same length as `X`. |
| `fit_transform(X, y=None, ensure_all_finite=True, **kwargs)` | Fit and return the embedding. | Returns `(embedding, rad_orig, rad_emb)` when `output_dens=True`. |
| `transform(X, ensure_all_finite=True)` | Project new rows into a standard UMAP embedding. | Not supported for densMAP-fitted models. |
| `inverse_transform(X)` | Invert standard embeddings when the fitted metric supports it. | Not available for densMAP. |
| `update(X, ensure_all_finite=True)` | Incrementally add rows for supported unsupervised models. | Supervised models cannot be updated in place. |

## Supervised target parameters

| Parameter | Default | Meaning | Practical guidance |
| --- | --- | --- | --- |
| `target_metric` | `"categorical"` | Distance metric for target values. | Use categorical for class labels; use numeric metrics such as `l1` or `l2` for continuous targets. |
| `target_metric_kwds` | `None` | Keyword arguments passed to the target metric. | Keep `None` unless the chosen target metric requires options. |
| `target_n_neighbors` | `-1` | Number of neighbors for the target simplicial set. | `-1` reuses the feature-side `n_neighbors`; otherwise choose `>= 2`. |
| `target_weight` | `0.5` | Blend between data topology and target topology. | Lower values preserve more feature geometry; higher values make labels dominate more. |

Target metric choices observed in package tests include categorical labels,
string labels, discrete/ordinal/count-style labels, and numeric metrics such as
`l1`. Treat this as evidence that target type and metric must match.

## Semi-supervised labels

For `target_metric="categorical"`, label value `-1` is interpreted as
unlabeled. This is the supported convention to preserve for partial-label class
workflows.

Checklist:

- `len(y) == X.shape[0]` after filtering, splitting, or sampling.
- Unknown labels are consistently encoded as `-1` only for categorical targets.
- Label dtype is consistent; do not accidentally mix strings, integers, and
  missing values.
- `target_weight` is tuned with validation, especially when many labels are
  unknown or noisy.

## densMAP parameters

| Parameter | Default | Meaning | Validation |
| --- | --- | --- | --- |
| `densmap` | `False` | Enables the density-augmented objective. | Use only when density preservation is part of the task. |
| `dens_lambda` | `2.0` | Weight of density regularization. | Must be non-negative. Higher values prioritize density preservation. |
| `dens_frac` | `0.3` | Fraction of epochs using the density objective. | Must be between `0.0` and `1.0`. |
| `dens_var_shift` | `0.1` | Stabilizer in density-variance calculations. | Must be non-negative. |
| `output_dens` | `False` | Computes and returns local radii. | Can be used with or without `densmap=True`. |

When `output_dens=True`, `fit_transform` returns:

```python
embedding, rad_orig, rad_emb = mapper.fit_transform(X, y)
```

After `fit`, the same radii are available as `mapper.rad_orig_` and
`mapper.rad_emb_`.

## Outputs and attributes

| Attribute/output | Meaning | When available |
| --- | --- | --- |
| `embedding_` | Learned low-dimensional coordinates. | After `fit` or `fit_transform`. |
| `rad_orig_` | Log-transformed local radius in original data space. | After fitting with `output_dens=True`. |
| `rad_emb_` | Log-transformed local radius in embedding space. | After fitting with `output_dens=True`. |
| `_supervised` | Internal flag indicating a supervised fit. | Internal/debug only; do not rely on it as public API. |

## Known limitations to plan around

- DensMAP transform into an existing embedding raises `NotImplementedError`.
- DensMAP inverse transform raises `ValueError`.
- Updating supervised models raises `ValueError`.
- `output_dens=True` changes the return type of `fit_transform`; unpack the
  tuple before passing the embedding to clustering or plotting.
- UMAP does not include a clustering estimator. KMeans, HDBSCAN, and LOF are
  separate downstream tools and need their own validation.
