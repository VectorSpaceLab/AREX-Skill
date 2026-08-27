# Pipeline Reference

This reference covers the public pipeline-facing APIs, model-spec grammar,
registries, canonical order, `return_model` behavior, and replay contract.

## Public API signatures

| Entry point | Signature | Notes |
| --- | --- | --- |
| `hypertools.analyze` | `analyze(data, manip=None, normalize=None, reduce=None, ndims=None, align=None, cluster=None, pipeline=None, return_model=False, internal=False, impute=None, random_state=None)` | Canonical multi-stage dispatcher and replay path. |
| `hypertools.manip` | `manip(data, model='ZScore', return_model=False, normalize=None, reduce=None, ndims=None, align=None, cluster=None, **kwargs)` | Manipulator dispatcher; can chain into the full pipeline. |
| `hypertools.normalize` | `normalize(x, normalize='across', internal=False, format_data=True, impute=None, return_model=False, manip=None, reduce=None, ndims=None, align=None, cluster=None, model=None)` | Z-score dispatcher with `model=` alias. |
| `hypertools.reduce` | `reduce(x, reduce='IncrementalPCA', ndims=None, return_model=False, manip=None, normalize=None, align=None, cluster=None, internal=False, format_data=True, random_state=None, model=None)` | Dimensionality reduction dispatcher with `model=` alias. |
| `hypertools.align` | `align(data, model='HyperAlign', return_model=False, manip=None, normalize=None, reduce=None, ndims=None, cluster=None, format_data=True, **kwargs)` | Alignment dispatcher; `align=` kwarg alias is deprecated here. |
| `hypertools.cluster` | `cluster(x, cluster='KMeans', n_clusters=None, return_model=False, manip=None, normalize=None, reduce=None, ndims=None, align=None, format_data=True, random_state=None, model=None)` | Hard labels or soft memberships depending on model family. |
| `hypertools.apply_model` | `apply_model(data, model, mode='auto', return_model=False, format_data=True, stack=True, ndims=None)` | Applies reduce/cluster families to stacked or per-dataset data. |
| `hypertools.Pipeline` | `Pipeline(steps)` | Reusable chain of resolved steps. |

## Supported model-spec grammar

All of the stage dispatchers accept the same core model-spec forms, with a few
stage-specific aliases.

```text
spec := str | class | instance | dict | list[spec]

dict := {
  'model': spec,
  'args'?: list,
  'kwargs'?: dict,
}
legacy dict := {
  'model': spec,
  'params': dict,
}
```

Important details:

- `args` and `kwargs` are optional in the canonical dict form.
- Legacy `params` is still accepted, but it warns.
- `Pipeline` also accepts nested `Pipeline` instances and bare step specs.
- `manip` accepts a `list` whose entries may include manipulator names as well
  as reduce/align/cluster names; inside that list, names are resolved in the
  order manip -> reduce -> align -> cluster.
- `normalize`, `reduce`, `align`, and `cluster` also accept fitted wrappers or
  fitted `Pipeline` objects when replaying on new data.

## Registry map

| Stage | Registry / names | Notes |
| --- | --- | --- |
| `manip` | `MANIPULATORS = [Normalize, ZScore, Smooth, Resample]` | DataFrame-based manipulators. `ZScore` and `Normalize` share statistics across a list input; `Smooth` and `Resample` run per dataset. |
| `normalize` | `'across'`, `'within'`, `'row'`, or a fitted `Normalizer` | `model=` is an alias for `normalize=`. |
| `reduce` | `REDUCERS`, `models`, `AUTOENCODER_NAMES`, `'UMAP'` | Includes classic reducers, mixture models, and optional torch autoencoders. `supported_models()` returns the reduce+cluster registry names plus `UMAP`. |
| `align` | `ALIGNERS = [HyperAlign, SharedResponseModel, DeterministicSharedResponseModel, RobustSharedResponseModel, Procrustes, NullAlign]` | `'hyper'` is a deprecated alias for `HyperAlign` in `align(model=...)`; `align=` as a kwarg alias is also deprecated on `align()`. |
| `cluster` | `CLUSTERERS` and `MIXTURES` | Hard clusterers return labels; mixture models return membership proportions. |
| `apply_model` | reduce + cluster families only | `apply_model` intentionally does not cover manip/align/forecast/impute families. |

## Canonical order and routing

When dispatcher kwargs are combined, HyperTools always constructs the same stage
order:

`manip -> normalize -> reduce -> align -> cluster`

A few consequences matter in practice:

- `analyze(..., return_model=True)` and similar cross-module calls hand back a
  fitted `Pipeline` when more than one stage ran.
- The stage kwargs are run in that fixed order even if the function called is
  `normalize`, `reduce`, `align`, or `cluster`.
- `pipeline=` on `analyze` replays an already-fitted chain instead of refitting
  it.
- `apply_model` is separate and uses its own fit/apply rule.

## `apply_model` model family and mode behavior

`apply_model` is for the stacked-array / single-model core.

### Accepted model families

- Reduce family: PCA, IncrementalPCA, SparsePCA, MiniBatchSparsePCA,
  KernelPCA, FastICA, FactorAnalysis, TruncatedSVD, DictionaryLearning,
  MiniBatchDictionaryLearning, TSNE, Isomap, SpectralEmbedding,
  LocallyLinearEmbedding, MDS, UMAP, plus the mixture models and optional
  autoencoders when installed.
- Cluster family: KMeans, MiniBatchKMeans, AgglomerativeClustering, Birch,
  FeatureAgglomeration, SpectralClustering, HDBSCAN, MeanShift, DBSCAN,
  OPTICS, AffinityPropagation, GaussianMixture, BayesianGaussianMixture,
  LatentDirichletAllocation, NMF.

### Modes

| Mode | Meaning |
| --- | --- |
| `auto` | Prefer `predict_proba`, then `fit_transform` / `transform`, then `fit_predict`. |
| `fit_transform` | Fit and transform. |
| `fit_predict` | Fit and return labels. |
| `predict_proba` | Fit and return probabilities. |

### Stack behavior

- `stack=True` vertically stacks all datasets, fits once, then splits the
  result back to match the input structure.
- `stack=False` fits one clone per dataset.
- `return_model=True` returns the fitted model(s) alongside the result.
- For a list spec, `return_model=True` returns a fitted `Pipeline`.

## `Pipeline` replay contract

`Pipeline` is a resolved, scikit-learn-style chain.

- `Pipeline.fit_transform` refits every step from scratch.
- `Pipeline.transform` reuses already-fitted steps.
- Steps with only `fit_predict` may refit on new data and warn.
- Steps with no out-of-sample path raise a clear error.
- `Pipeline.inverse_transform` walks the chain in reverse and stops at the first
  step that cannot invert.

Because `Pipeline` stores resolved instances, a fitted wrapper or fitted
`Pipeline` can be passed back in directly as the model spec for the relevant
stage dispatcher.

## `return_model` reuse contract

| Dispatcher shape | `return_model=False` | `return_model=True` |
| --- | --- | --- |
| Single stage only | Transformed data. | Fitted stage wrapper. |
| Multiple stages / cross-module kwargs | Transformed data. | Fitted `Pipeline`. |
| `cluster` with `cluster=None` or `False` | Input unchanged. | `(input, None)`. |
| `reduce` with no actual reduction | Input unchanged. | `(input, None)`. |
| `analyze(pipeline=...)` replay path | Reuses the fitted pipeline. | Returns `(result, pipeline)`. |

When the last step is `cluster`, remember that `analyze` still returns the
transformed data, not the labels. Recover labels from the fitted cluster step:

```python
labels = pipeline.named_steps['cluster'].transform(transformed_data)
```

## `ndims` and `random_state`

- `ndims` must be a positive integer or `None`.
- For `reduce`, `ndims` becomes `n_components` on models that accept it.
- For `cluster`, `ndims` only matters when `reduce=` is also present.
- `analyze`, `reduce`, and `cluster` thread `random_state` into stochastic
  reduce/cluster models when supported.
- `apply_model` has no `random_state=` parameter.

## `impute=` note

There is no dedicated pipeline stage for imputation here. Missing-value fill is
handled at format time via `impute=` and should be routed to the forecasting /
imputation sub-skill when the question is really about those model families.
