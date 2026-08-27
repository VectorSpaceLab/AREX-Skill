# API Reference

## Purpose

This file captures the verified constructor signatures and call patterns for the global tabular explainers.

## Constructors

- `ALE(predictor, feature_names=None, target_names=None, check_feature_resolution=True, low_resolution_threshold=10, extrapolate_constant=True, extrapolate_constant_perc=10.0, extrapolate_constant_min=0.1)`
- `PartialDependence(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `TreePartialDependence(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `PartialDependenceVariance(predictor, feature_names=None, categorical_names=None, target_names=None, verbose=False)`
- `PermutationImportance(predictor, loss_fns=None, score_fns=None, feature_names=None, verbose=False)`

## Explainers

- `ALE.explain(X, features=None, min_bin_points=4, grid_points=None)`
- `PartialDependence.explain(X, features=None, kind='average', percentiles=(0.0, 1.0), grid_resolution=100, grid_points=None)`
- `TreePartialDependence.explain(X, features=None, percentiles=(0.0, 1.0), grid_resolution=100, grid_points=None)`
- `PartialDependenceVariance.explain(X, features=None, method='importance', percentiles=(0.0, 1.0), grid_resolution=100, grid_points=None)`
- `PermutationImportance.explain(X, y, features=None, method='estimate', kind='ratio', n_repeats=50, sample_weight=None)`

## Plot helpers

- `plot_ale(exp, features='all', targets='all', ... )`
- `plot_pd(exp, features='all', targets='all', ... )`
- `plot_pd_variance(exp, summarise=True, ... )`
- `plot_permutation_importance(exp, ... )`

## Output shapes

- ALE returns ALE values plus centering and feature-value metadata.
- Partial dependence returns PD values and, for the black-box variant, ICE values.
- PD variance returns scalar importance or interaction summaries and per-feature PD data.
- Permutation importance returns feature importances keyed by metric.

## Notes

- These APIs expect batched `numpy.ndarray` inputs.
- The predictor should return a `numpy` output compatible with the chosen metric.
- If a categorical feature is present, keep its encoded column indices and human-readable names aligned.
