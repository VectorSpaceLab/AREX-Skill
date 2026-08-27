---
name: umap-learn
description: "Use the umap-learn package for UMAP dimensionality reduction,
  supervised and density workflows, aligned embeddings, plotting, and
  ParametricUMAP."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# umap-learn Repo Skill

Use this repo skill when a task asks how to use `umap-learn` / `umap` for
Uniform Manifold Approximation and Projection: dimensionality reduction,
visualization embeddings, transform workflows, supervised UMAP, densMAP,
aligned embeddings, optional plotting, or optional ParametricUMAP.

## Install and Import

```bash
pip install umap-learn
```

```python
import umap
mapper = umap.UMAP()
```

Package facts:

- Distribution name: `umap-learn`.
- Import package: `umap`.
- Python requirement: `>=3.10` in package metadata.
- Base dependencies: numpy, scipy, scikit-learn, numba, pynndescent, and tqdm.
- No package console entry points are exposed; workflows are Python API based.

Optional extras:

```bash
pip install "umap-learn[plot]"           # umap.plot helpers
pip install "umap-learn[parametric_umap]" # TensorFlow/Keras ParametricUMAP
pip install "umap-learn[tbb]"            # optional CPU optimization
```

Run [`scripts/check_umap_environment.py`](scripts/check_umap_environment.py) to
inspect a target environment and optional extras:

```bash
python scripts/check_umap_environment.py --json
```

## Route Map

| Task | Read |
| --- | --- |
| Fit a standard UMAP embedding, tune base parameters, transform new rows, inverse transform, use sparse/precomputed inputs, or debug core API errors | [core-embedding](sub-skills/core-embedding/SKILL.md) |
| Use supervised labels, semi-supervised targets, densMAP, density outputs, clustering interpretation, or outlier analysis | [supervised-density](sub-skills/supervised-density/SKILL.md) |
| Align related slices/time periods, update aligned embeddings, or combine fitted UMAP models with intersection/union/contrast operators | [aligned-composition](sub-skills/aligned-composition/SKILL.md) |
| Use `umap.plot` points/connectivity/diagnostic/interactive helpers or fix optional plotting dependency failures | [plotting-diagnostics](sub-skills/plotting-diagnostics/SKILL.md) |
| Use optional TensorFlow/Keras `ParametricUMAP`, neural encoders/decoders, reconstruction, save/load, callbacks, landmarks, or ONNX export | [parametric-umap](sub-skills/parametric-umap/SKILL.md) |

## Fast Decision Guide

- Start with `umap.UMAP(random_state=42)` on a sample while debugging; remove
  the seed later if speed matters more than reproducibility.
- Use `n_neighbors` for local/global neighbourhood balance and `min_dist` for
  embedding compactness.
- Use `fit`/`fit_transform` on training data and `transform` on held-out data;
  check precomputed-distance shape contracts before using `metric="precomputed"`.
- Use `fit(X, y)` only when labels should influence the manifold; validate with
  a downstream metric rather than only a visually separated plot.
- Use densMAP only when density preservation is part of the question; some
  transform/inverse paths are intentionally unavailable for densMAP.
- Treat plotting and ParametricUMAP as optional extras. Missing optional
  dependencies should produce actionable install guidance, not block base UMAP.
- Do not claim CUDA/GPU acceleration for base `umap-learn`. Visible hardware is
  irrelevant unless a separate optional neural backend is installed and verified.

## Shared References

- Read [installation and environment](references/installation-and-environment.md)
  before setting up package dependencies or optional extras.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for
  install/import, optional extras, performance, and staleness checks.
- Read [repository provenance](references/repo-provenance.md) before deciding
  whether this generated skill is current for a checkout.

## Minimal Import Check

```python
import umap
print(umap.__version__)
print(umap.UMAP(n_neighbors=5, n_epochs=10, random_state=42))
```

For a runnable toy-data check, use the core sub-skill smoke script:

```bash
python sub-skills/core-embedding/scripts/umap_core_smoke.py --transform --json
```
