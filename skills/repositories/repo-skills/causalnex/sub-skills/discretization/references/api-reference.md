# Discretization API Reference

## Unsupervised discretizer

- `Discretiser(method="uniform", num_buckets=None, outlier_percentile=None, numeric_split_points=None, percentile_split_points=None)`
- `fit(data)`
- `transform(data)`
- `fit_transform(data)`

Supported methods:
- `uniform`
- `quantile`
- `outlier`
- `fixed`
- `percentiles`

## Supervised discretizers

- `DecisionTreeSupervisedDiscretiserMethod(mode="single", split_unselected_feat=False, tree_params=None)`
- `DecisionTreeSupervisedDiscretiserMethod.fit(feat_names, target, dataframe, target_continuous)`
- `MDLPSupervisedDiscretiserMethod(mdlp_args=None)`
- `MDLPSupervisedDiscretiserMethod.fit(feat_names, dataframe, target, target_continuous)`

## Helper behavior

- `DecisionTreeSupervisedDiscretiserMethod.map_thresholds` stores the learned split points per feature.
- `MDLPSupervisedDiscretiserMethod` raises `ImportError` if `mdlp-discretization` is missing.
- `extract_thresholds_from_dtree(dtree, length_df)` is the lower-level helper used by the tree-based method.

## BN classifier integration

`BayesianNetworkClassifier` uses the discretizers through:
- `discretiser_alg`: `unsupervised`, `tree`, or `mdlp`
- `discretiser_kwargs`: per-column constructor arguments

The keys of `discretiser_alg` and `discretiser_kwargs` must match exactly.
