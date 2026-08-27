---
name: feature-extraction-and-images
description: "Routes pyts feature extraction, image transforms, and
  singular-spectrum decomposition workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# feature-extraction-and-images

Use this sub-skill when a user wants to turn time series into feature vectors,
images, or SSA components before fitting a downstream model.

## What this covers

- Feature extraction transformers: `BagOfPatterns`, `BOSS`, `ROCKET`,
  `ShapeletTransform`, `WEASEL`.
- Image transforms: `GramianAngularField`, `MarkovTransitionField`,
  `RecurrencePlot`.
- Decomposition: `SingularSpectrumAnalysis`.
- Output shape, sparsity, flattening, and runtime-cost trade-offs for feature
  and image workflows.

## What this excludes

- Dataset loading: use `../datasets-and-loaders/SKILL.md`.
- Preprocessing and symbolic building blocks: use
  `../preprocessing-and-symbols/SKILL.md`.
- Metrics and classifiers: use `../metrics-and-classifiers/SKILL.md`.
- Multivariate wrappers such as `JointRecurrencePlot` and `WEASELMUSE`:
  use `../multivariate-workflows/SKILL.md`.

## Start here

1. Read `references/workflows.md` for the common feature/image recipes.
2. Read `references/api-reference.md` for the verified signatures and shape
   notes.
3. Read `references/troubleshooting.md` for kernel-size, sparse-output, and
   flattening issues.
4. Run `scripts/smoke.py` to confirm the installed package on a tiny
   feature/image/decomposition case.

## Useful triggers

- "ROCKET on GunPoint"
- "convert a series to a Gramian Angular Field"
- "shapelet transform output shape"
- "BOSS or WEASEL feature extraction"
- "SSA on a time series"

## Routing hints

- If the user needs a classifier after feature extraction, route there after
  you choose the transform and confirm the output shape.
- If the user needs the multivariate versions of these ideas, hand off to
  `../multivariate-workflows/SKILL.md` instead of expanding this sub-skill.
- If the user only wants a quick feature smoke test, use the bundled smoke
  script and tiny arrays rather than a full benchmark.

## Links

- Read `references/workflows.md` for recipes that chain feature extraction,
  images, and SSA.
- Read `references/api-reference.md` for the verified object signatures and key
  defaults.
- Read `references/troubleshooting.md` for kernel-size, shape, and sparsity
  failures.
- Run `scripts/smoke.py` for a quick installed-package check.
