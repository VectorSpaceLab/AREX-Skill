# Pipeline Troubleshooting

## Unknown model name

**Symptom**

- `unknown reduce model 'Bogus'`
- `unknown cluster model 'Foo'`
- `unknown align model 'Bar'`
- `unknown manip model 'Baz'`
- `apply_model` says the model family is unsupported.

**Likely cause**

- The model name is misspelled.
- The model belongs to a different dispatcher family.
- `apply_model` was used for a manipulator, aligner, forecaster, or imputer.

**Fix**

- Use the stage-specific dispatcher.
- For `apply_model`, stick to reduce/cluster families and `UMAP`.
- Check the relevant registry names in `references/pipeline-reference.md`.

## Dict spec mistakes

**Symptom**

- A dict spec warns about `params`.
- Constructor arguments seem to be ignored.
- `dict model specs require a 'model' key`.

**Likely cause**

- The legacy `{'model': ..., 'params': {...}}` form was used.
- `args` were placed on an already-constructed instance.
- `kwargs` were placed outside the `model` dict.

**Fix**

- Use the canonical form: `{'model': ..., 'args': [...], 'kwargs': {...}}`.
- Move constructor arguments into the `kwargs` block unless you are passing a
  bare class.
- For `cluster`, `n_clusters` may also live at the top level of the dict.
- For `align`, prefer `model=` and reserve the deprecated `align=` kwarg only
  for migration work.

## `ndims` looks ignored

**Symptom**

- `ndims` produces no visible effect.
- `cluster()` warns that `ndims` was passed but no reduction was requested.
- `reduce()` returns the input unchanged and `return_model=True` yields `None`.

**Likely cause**

- No `reduce=` stage was present.
- `ndims` was larger than the input width, so reduction became a no-op.
- A reducer without an out-of-sample path was replayed on new data.

**Fix**

- Supply a reduce model and a smaller `ndims`.
- Remember that `cluster` only uses `ndims` when `reduce=` is also present.
- Choose a transformable reducer if you need reuse on new data.

## Reuse fails for TSNE / MDS / SpectralEmbedding

**Symptom**

- `NotImplementedError` or a clear transform error on held-out data.

**Likely cause**

- The fitted reducer has no out-of-sample transform.

**Fix**

- Refit on the new data.
- Or switch to a transformable reducer such as PCA or UMAP.
- The error is expected: these models can fit only the data they saw.

## Normalize or ZScore column mismatch

**Symptom**

- Reusing a fitted `Normalizer` / `ZScore` raises a width mismatch error.
- The new data has a different number of columns than the fit-time data.

**Likely cause**

- The reuse path is positional, not label-based.
- The new data does not have the same feature width.

**Fix**

- Align the feature set before reusing the fitted model.
- Or refit on the new data.
- Column labels may differ, but column count must match.

## Alignment shape mismatch

**Symptom**

- `aligner was fit on ... dataset(s)`
- `aligner was fit on ... column(s)`
- `datasets share no common row-index values`

**Likely cause**

- The held-out data has a different number of datasets.
- The per-dataset column counts changed.
- The input indices share no common rows.

**Fix**

- Keep the same number of datasets and feature widths when replaying an
  aligner.
- Reindex the data if row matching is supposed to work by position.
- Refit if the structure is genuinely different.

## Cluster labels vs transformed data

**Symptom**

- `analyze(..., cluster=...)` returns data, not labels.
- `plot(..., return_model=True)` returns a bundle, not raw labels.

**Likely cause**

- This is the documented contract.

**Fix**

- Read labels or membership weights from
  `pipeline.named_steps['cluster'].transform(transformed_data)`.
- Or call `cluster(...)` directly if you only want clustering output.

## Hard clusterer reuse warnings

**Symptom**

- Reusing a hard clusterer on same-shape but different data warns.
- Reusing on different row counts raises `NotImplementedError`.

**Likely cause**

- Hard clusterers without `predict` can only safely recover fit-time labels.

**Fix**

- Refit on the new data if the content changed.
- Treat the warning as a signal that labels were replayed, not recomputed.

## Legacy argument deprecations

**Symptom**

- `DeprecationWarning` mentions `params`.
- `align=True` raises an error.
- A deprecated alias is mentioned in the warning text.

**Likely cause**

- Old call forms are being used.

**Fix**

- Replace legacy dict specs with `{'model': ..., 'args': [...], 'kwargs': {...}}`.
- Replace `align=True` with an explicit algorithm name such as `align='HyperAlign'`.
- Prefer canonical names such as `HyperAlign` rather than deprecated aliases.

## Row-wise manip reuse

**Symptom**

- Reusing a fitted `ZScore` or `Normalize` with `axis=1` raises `NotImplementedError`.

**Likely cause**

- Row-wise statistics are tied to the fit-time rows.

**Fix**

- Refit on the new data.
- Use `Resample` if you need a manipulator that re-derives its state from the
  new input.
