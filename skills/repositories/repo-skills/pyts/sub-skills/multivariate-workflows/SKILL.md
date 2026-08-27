---
name: multivariate-workflows
description: "Routes pyts multivariate transformer, classifier, image, and
  validation workflows for 3D time-series inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# multivariate-workflows

Use this sub-skill when the input has a feature/channel axis and the task is to
wrap a univariate pyts estimator for multivariate data or use a multivariate
specific transform.

## What this covers

- `MultivariateTransformer` for wrapping univariate transformers.
- `MultivariateClassifier` for wrapping univariate classifiers.
- `WEASELMUSE` for multivariate symbolic feature extraction.
- `JointRecurrencePlot` for multivariate recurrence images.
- `check_3d_array` for shape validation.

## What this excludes

- Univariate dataset loading: use `../datasets-and-loaders/SKILL.md`.
- Univariate preprocessing and symbolic encoders: use
  `../preprocessing-and-symbols/SKILL.md`.
- Univariate feature extraction and image transforms: use
  `../feature-extraction-and-images/SKILL.md`.
- Univariate metrics and classifiers: use `../metrics-and-classifiers/SKILL.md`.

## Start here

1. Read `references/workflows.md` for the multivariate recipes and shape
   expectations.
2. Read `references/api-reference.md` for the verified signatures.
3. Read `references/troubleshooting.md` for 2D-vs-3D and flattening problems.
4. Run `scripts/smoke.py` to confirm the installed package on a tiny
   multivariate case.

## Useful triggers

- "wrap a transformer for multivariate time series"
- "BasicMotions with pyts"
- "multivariate recurrence plot"
- "WEASELMUSE"
- "why does my input need to be 3D?"

## Routing hints

- If the user has a 2D array but mentions multiple channels, clarify the
  intended axis order before modeling.
- If the user needs a multivariate image or classifier, route here even when
  the underlying estimator is a univariate pyts object.
- If the user needs a downstream classifier after multivariate transformation,
  keep the wrapper choice in this sub-skill and then hand off to the model the
  wrapper contains.

## Links

- Read `references/workflows.md` for the canonical 3D input recipes.
- Read `references/api-reference.md` for the verified signatures and defaults.
- Read `references/troubleshooting.md` for shape and output-size pitfalls.
- Run `scripts/smoke.py` for a quick installed-package check.
