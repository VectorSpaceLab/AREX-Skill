---
name: decomposition
description: "Routes scikit-plot PCA visualization requests for
  component-variance and 2-D projection plots."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Decomposition

Use this sub-skill for the `scikitplot.decomposition` PCA visualization functions. These routes expect a fitted PCA-like estimator and return Matplotlib `Axes` objects.

## Route here

- Plot cumulative explained variance with `plot_pca_component_variance`.
- Plot a labeled 2-D PCA projection with `plot_pca_2d_projection`.
- Add biplot vectors and feature labels when the fitted estimator exposes component vectors.
- Validate the route quickly with `scripts/decomposition_smoke.py`.

## Inputs to check first

1. Fit the PCA estimator before plotting.
2. For component variance, confirm the estimator has `explained_variance_ratio_`.
3. For 2-D projection, confirm the estimator has `transform(X)` and produces at least two coordinates.
4. For biplots, confirm `components_[:2, :]` exists and `feature_labels`, if supplied, align with input features.
5. Pass `ax=` when embedding into a figure layout.

## Common decisions

- Use `target_explained_variance` to highlight the minimum component count that reaches a target cumulative ratio.
- Use `cmap` to choose class colors in projection plots.
- Use `biplot=True` only when feature vectors are meaningful and the plot will not be too crowded.
- Keep the PCA and data matrix in the same preprocessing space used during `fit`.

## Reroute

- Metric curves or silhouette analysis: `../metrics/SKILL.md`.
- Feature importances or learning curves: `../estimators/SKILL.md`.
- Elbow curves for clusterers: `../clustering/SKILL.md`.
- Legacy `scikitplot.plotters` calls to PCA helpers: `../legacy-factories/SKILL.md`.

## Read next

- `references/api-reference.md` for verified signatures and estimator requirements.
- `references/workflows.md` for component-variance and projection recipes.
- `references/troubleshooting.md` for unfitted PCA, missing attributes, biplot, and Axes errors.
- `scripts/decomposition_smoke.py` for a tiny Agg-backed PCA smoke run.
