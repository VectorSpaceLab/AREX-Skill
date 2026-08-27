---
name: clustering
description: "Guides pomegranate KMeans clustering workflows, including centroid
  initialization, fit/predict APIs, sample weights, initialization choices,
  convergence controls, and KMeans troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# clustering

## Use this sub-skill when

Use this sub-skill for the pomegranate `KMeans` class as a standalone clusterer or as the initialization mechanism used by mixture and HMM workflows. It covers centroid initialization, `fit`, `predict`, `fit_predict`, sample weights, convergence controls, and common shape/initialization failures.

## Start here

Typical import:

```python
from pomegranate.kmeans import KMeans
```

Read [references/api-reference.md](references/api-reference.md) for constructor parameters, initialization options, and usage examples. Run [scripts/smoke_kmeans.py](scripts/smoke_kmeans.py) after installation for a tiny deterministic smoke check.

## Core workflow

1. **Choose `k` or explicit centroids.** Provide `k` to initialize from data or `centroids` to start from known centers.
2. **Use 2D numeric data.** KMeans expects `(n, d)` floating point features.
3. **Select initialization.** Start with `init='first-k'` for deterministic debugging or `init='random'` with `random_state` for randomized starts.
4. **Fit and predict.** Use `fit(X)`, `predict(X)`, or `fit_predict(X)` depending on whether you need cluster assignments immediately.
5. **Control convergence.** Use `max_iter`, `tol`, `inertia`, and `verbose` when diagnosing training behavior.

## Route elsewhere when

- KMeans is only an initializer inside `GeneralMixtureModel`: read [../mixtures-and-classifiers/SKILL.md](../mixtures-and-classifiers/SKILL.md) after checking the initialization choice here.
- KMeans initializes emissions inside HMM workflows: read [../sequence-models/SKILL.md](../sequence-models/SKILL.md).
- The task is probability scoring or sampling rather than clustering: use the relevant probabilistic model sub-skill.

## Guardrails

- `k` must be at least 2 when centroids are not provided.
- Component labels are arbitrary cluster ids; do not compare labels across independent fits without matching centroids.
- Submodular initialization options rely on `apricot-select`; use simpler initializers first when debugging.
- Read [references/troubleshooting.md](references/troubleshooting.md) when centroid shape, initialization, sample weights, masked data, or convergence is confusing.
