---
name: metrics-and-classifiers
description: "Routes pyts DTW, lower-bound, and time-series classifier workflows
  for univariate series."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# metrics-and-classifiers

Use this sub-skill when the task is to compare two series with DTW/BOSS,
choose a time-series metric, or fit a pyts classifier on univariate data.

## What this covers

- Metrics and regions: `boss`, `dtw`, `sakoe_chiba_band`,
  `itakura_parallelogram`, `show_options`, and the DTW lower bounds.
- Classifiers: `KNeighborsClassifier`, `BOSSVS`, `SAXVSM`,
  `TimeSeriesForest`, `TSBF`, `LearningShapelets`.
- Metric-aware classification recipes such as `metric='dtw'` on GunPoint.
- Practical compatibility and performance notes for Numba and scikit-learn.

## What this excludes

- Dataset loading: use `../datasets-and-loaders/SKILL.md`.
- Preprocessing and symbolic building blocks: use
  `../preprocessing-and-symbols/SKILL.md`.
- Feature extraction, images, and SSA: use
  `../feature-extraction-and-images/SKILL.md`.
- Multivariate wrappers: use `../multivariate-workflows/SKILL.md`.

## Start here

1. Read `references/workflows.md` for the best-fit metric and classifier
   recipes.
2. Read `references/api-reference.md` for the verified signatures and option
   names.
3. Read `references/troubleshooting.md` when a DTW or classifier call fails on
   version skew, region shapes, or training cost.
4. Run `scripts/smoke.py` to confirm the installed package with a tiny
   metric/classifier check.

## Useful triggers

- "DTW between two time series"
- "which Sakoe-Chiba band should I use?"
- "fit KNeighborsClassifier with dtw"
- "SAXVSM or BOSSVS on GunPoint"
- "why does dtw suddenly break after upgrading scikit-learn?"

## Routing hints

- If the user only needs a pairwise distance, stay on the metric half of this
  sub-skill.
- If the user wants a classifier, route to the classifier half only after the
  metric or representation choice is clear.
- If the task is really about preprocessing or symbolic building blocks for a
  classifier, route there first and then return here for the modeling step.

## Links

- Read `references/workflows.md` for the default DTW and classifier recipes.
- Read `references/api-reference.md` for the verified metric and classifier
  signatures.
- Read `references/troubleshooting.md` for the scikit-learn compatibility and
  DTW shape pitfalls.
- Run `scripts/smoke.py` for a quick installed-package check.
