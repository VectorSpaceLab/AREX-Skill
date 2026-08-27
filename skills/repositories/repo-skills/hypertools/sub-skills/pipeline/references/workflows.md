# Pipeline Workflows

This file collects the common pipeline recipes future agents should reach for
first.

## 1) Fit once, reuse later

Use this pattern when you want one fitted chain and then the same learned
transformation on held-out data.

```python
import numpy as np
import hypertools as hyp

train = [np.random.default_rng(0).normal(size=(12, 6)),
         np.random.default_rng(1).normal(size=(12, 6))]
held_out = [np.random.default_rng(2).normal(size=(12, 6)),
            np.random.default_rng(3).normal(size=(12, 6))]

result, pipeline = hyp.analyze(
    train,
    manip={'model': 'Smooth', 'kwargs': {'kernel_width': 5}},
    normalize='across',
    reduce='PCA',
    ndims=2,
    align={'model': 'HyperAlign', 'kwargs': {'n_iter': 2}},
    cluster={'model': 'GaussianMixture', 'kwargs': {'n_components': 2,
                                                    'random_state': 0}},
    random_state=0,
    return_model=True,
    internal=True,
)

reused, same_pipeline = hyp.analyze(
    held_out,
    pipeline=pipeline,
    return_model=True,
    internal=True,
)
```

### What to check

- `pipeline.is_fitted` is `True`.
- `same_pipeline is pipeline`.
- The fitted step order is `manip -> normalize -> reduce -> align -> cluster`.
- The replayed result has the same structural shape as the fit-time result.
- If you need cluster memberships, recover them from
  `pipeline.named_steps['cluster'].transform(np.vstack(result))`.

## 2) Build a reusable chain directly

Use `Pipeline(steps)` when you want the chain without going through a dispatcher.

```python
from hypertools import Pipeline

pipe = Pipeline([
    'ZScore',
    {'model': 'PCA', 'kwargs': {'n_components': 2}},
])

out = pipe.fit_transform(train[0])
again = pipe.transform(held_out[0])
```

### When to use `apply_model`

Use `apply_model` when you need the single-model stack/apply core, not the full
stage pipeline.

```python
from hypertools.core.model import apply_model

reduced, fitted = apply_model(train[0], 'PCA', ndims=2, return_model=True)
```

- `stack=True` fits once across all datasets.
- `stack=False` fits one clone per dataset.
- `return_model=True` on a list spec returns a fitted `Pipeline`.

## 3) Story trajectories and multi-subject time series

For trajectory-style data, keep the preprocessing steps in `manip`, then use the
canonical stage order to reduce dimensionality and align subjects.

Recommended shape of the call:

```python
fig_data, pipeline = hyp.analyze(
    subjects,
    manip={'model': 'Smooth', 'kwargs': {'kernel_width': 25}},
    normalize='across',
    reduce='PCA',
    ndims=2,
    align={'model': 'HyperAlign', 'kwargs': {'n_iter': 2}},
    return_model=True,
    internal=True,
)
```

### Practical guidance

- Use `Smooth` and/or `Resample` in `manip` before the geometry stages.
- Keep `reduce` before `align` in the canonical chain.
- If you need the exact same learned chain on another subject group, reuse the
  fitted `Pipeline` via `pipeline=`.
- If the task is about figures, animation, or backend appearance, switch to the
  sibling visualization sub-skill for the rendering part.

## 4) Clustering and soft mixtures

Use the cluster stage when the outcome is labels or membership weights.

```python
out, pipeline = hyp.analyze(
    train,
    normalize='across',
    reduce='PCA',
    ndims=2,
    cluster={'model': 'GaussianMixture', 'kwargs': {'n_components': 2,
                                                    'random_state': 0}},
    return_model=True,
)

probs = pipeline.named_steps['cluster'].transform(np.vstack(out))
```

### Notes

- Hard clusterers return labels.
- Mixture models return membership proportions.
- `FeatureAgglomeration` clusters columns, not rows.
- `analyze(cluster=...)` returns transformed data, not labels.
- Recovered labels / proportions come from the fitted cluster step.

## 5) Error-resistant reuse habits

- Keep the feature width identical when reusing `normalize`, `reduce`, or
  `align` results.
- Refit when you need a different number of features, dimensions, or subjects.
- Use `random_state` on stochastic reduce/cluster models when reproducibility
  matters.
- Use dict specs when you need constructor parameters and want to keep the call
  readable.
