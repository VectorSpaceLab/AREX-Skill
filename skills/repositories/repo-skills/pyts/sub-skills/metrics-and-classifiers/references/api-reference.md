# API Reference

## Verified public signatures

- `boss(x, y)`
- `dtw(x=None, y=None, dist='square', method='classic', options=None, precomputed_cost=None, return_cost=False, return_accumulated=False, return_path=False)`
- `itakura_parallelogram(n_timestamps_1, n_timestamps_2=None, max_slope=2.0)`
- `lower_bound_improved(X_train, X_test, region)`
- `lower_bound_keogh(X_train, X_test, region)`
- `lower_bound_kim(X_train, X_test)`
- `lower_bound_yi(X_train, X_test)`
- `sakoe_chiba_band(n_timestamps_1, n_timestamps_2=None, window_size=0.1)`
- `show_options(method=None, disp=True)`
- `KNeighborsClassifier(n_neighbors=1, weights='uniform', algorithm='auto', leaf_size=30, p=2, metric='minkowski', metric_params=None, n_jobs=1, **kwargs)`
- `BOSSVS(word_size=4, n_bins=4, window_size=10, window_step=1, anova=False, drop_sum=False, norm_mean=False, norm_std=False, strategy='quantile', alphabet=None, numerosity_reduction=True, use_idf=True, smooth_idf=False, sublinear_tf=True)`
- `SAXVSM(window_size=0.5, word_size=0.5, n_bins=4, strategy='normal', numerosity_reduction=True, window_step=1, threshold_std=0.01, norm_mean=True, norm_std=True, use_idf=True, smooth_idf=False, sublinear_tf=True, overlapping=True, alphabet=None)`
- `TimeSeriesForest(n_estimators=500, n_windows=1.0, min_window_size=1, criterion='entropy', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='sqrt', max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, class_weight=None, ccp_alpha=0.0, max_samples=None)`
- `TSBF(n_estimators=500, min_subsequence_size=0.5, min_interval_size=0.1, n_subsequences='auto', bins=10, criterion='entropy', max_depth=None, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='sqrt', max_leaf_nodes=None, min_impurity_decrease=0.0, bootstrap=True, oob_score=False, n_jobs=None, random_state=None, verbose=0, class_weight=None, ccp_alpha=0.0, max_samples=None)`
- `LearningShapelets(n_shapelets_per_size=0.2, min_shapelet_length=0.1, shapelet_scale=3, penalty='l2', tol=0.001, C=1000, learning_rate=1.0, max_iter=1000, multi_class='multinomial', alpha=-100, fit_intercept=True, intercept_scaling=1.0, class_weight=None, verbose=0, random_state=None, n_jobs=None)`

## Signature notes

- `boss` is a distance between two one-dimensional arrays of the same shape.
- `dtw` supports classic, region-based, Sakoe-Chiba, Itakura, multiscale, and
  fast methods via the `method` and `options` arguments.
- The classifiers are scikit-learn-style estimators: use `fit`, `predict`, and
  sometimes `score` as usual.
- `KNeighborsClassifier(metric='dtw')` is the simplest raw-time-series baseline
  in this repo.

## Documentation overlap

- Use the user guide for long-form metric variants and classifier examples.
- Use the bundled smoke script for a minimal reproducible installed-package
  check.
