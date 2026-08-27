# API Reference

## Verified public signatures

- `MultivariateTransformer(estimator, flatten=True)`
- `MultivariateClassifier(estimator, weights=None)`
- `WEASELMUSE(word_size=4, n_bins=4, window_sizes=[0.1, 0.3, 0.5, 0.7, 0.9], window_steps=None, anova=False, drop_sum=True, norm_mean=True, norm_std=True, strategy='quantile', chi2_threshold=2, sparse=True, alphabet=None)`
- `JointRecurrencePlot(dimension=1, time_delay=1, threshold=None, percentage=10)`
- `check_3d_array(X)`

## Shape notes

- `MultivariateTransformer` and `MultivariateClassifier` expect a 3D input
  array with sample, channel, and timestamp axes.
- `flatten=False` preserves the wrapped estimator's image-like output shape.
- `WEASELMUSE` returns a feature matrix; the smoke script shows that tiny
  inputs can still produce an empty or degenerate result if the thresholds are
  too aggressive.

## Usage notes

- Pick the wrapped univariate estimator first, then decide whether the output
  should remain image-like or flattened.
- `check_3d_array` is the earliest and cheapest place to catch a shape mistake.
