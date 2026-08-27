# API Reference

## Verified public signatures

- `BagOfPatterns(window_size=0.5, word_size=0.5, n_bins=4, strategy='normal', numerosity_reduction=True, window_step=1, norm_mean=True, norm_std=True, sparse=True, overlapping=True, alphabet=None)`
- `BOSS(word_size=4, n_bins=4, strategy='quantile', window_size=10, window_step=1, anova=False, drop_sum=False, norm_mean=False, norm_std=False, numerosity_reduction=True, sparse=True, alphabet=None)`
- `ROCKET(n_kernels=10000, kernel_sizes=(7, 9, 11), random_state=None)`
- `ShapeletTransform(n_shapelets='auto', criterion='mutual_info', window_sizes='auto', window_steps=None, remove_similar=True, sort=False, verbose=0, random_state=None, n_jobs=None)`
- `WEASEL(word_size=4, n_bins=4, window_sizes=[0.1, 0.3, 0.5, 0.7, 0.9], window_steps=None, anova=True, drop_sum=True, norm_mean=True, norm_std=True, strategy='entropy', chi2_threshold=2, sparse=True, alphabet=None)`
- `GramianAngularField(image_size=1.0, sample_range=(-1, 1), method='summation', overlapping=False, flatten=False)`
- `MarkovTransitionField(image_size=1.0, n_bins=8, strategy='quantile', overlapping=False, flatten=False)`
- `RecurrencePlot(dimension=1, time_delay=1, threshold=None, percentage=10, flatten=False)`
- `SingularSpectrumAnalysis(window_size=4, groups=None, lower_frequency_bound=0.075, lower_frequency_contribution=0.85, chunksize=None, n_jobs=1)`

## Shape notes

- The feature extractors output a feature matrix suitable for a downstream
  scikit-learn estimator.
- The image transformers output image-like arrays, unless `flatten=True` on the
  transform that supports flattening.
- `SingularSpectrumAnalysis` returns decomposed component series, not a
  classifier-ready feature matrix.

## Usage notes

- `ROCKET` and `ShapeletTransform` are the most likely to be runtime-heavy, so
  shrink their parameters first when debugging.
- `WEASEL` can produce sparse or empty outputs on tiny inputs if the
  discretization settings are too aggressive.
- `BagOfPatterns` and `BOSS` depend on the symbolic building blocks from the
  preprocessing sub-skill.
