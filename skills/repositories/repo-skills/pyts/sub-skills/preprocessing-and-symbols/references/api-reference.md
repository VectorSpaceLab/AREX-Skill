# API Reference

## Verified public signatures

- `StandardScaler(with_mean=True, with_std=True)`
- `MinMaxScaler(sample_range=(0, 1))`
- `MaxAbsScaler()`
- `RobustScaler(with_centering=True, with_scaling=True, quantile_range=(25.0, 75.0))`
- `PowerTransformer(method='yeo-johnson', standardize=True)`
- `QuantileTransformer(n_quantiles=1000, output_distribution='uniform', subsample=100000, random_state=None)`
- `KBinsDiscretizer(n_bins=5, strategy='quantile', raise_warning=True)`
- `InterpolationImputer(missing_values=nan, strategy='linear')`
- `PiecewiseAggregateApproximation(window_size=1, output_size=None, overlapping=True)`
- `SymbolicAggregateApproximation(n_bins=4, strategy='quantile', raise_warning=True, alphabet=None)`
- `DiscreteFourierTransform(n_coefs=None, drop_sum=False, anova=False, norm_mean=False, norm_std=False)`
- `MultipleCoefficientBinning(n_bins=4, strategy='quantile', alphabet=None)`
- `SymbolicFourierApproximation(n_coefs=None, n_bins=4, strategy='quantile', drop_sum=False, anova=False, norm_mean=False, norm_std=False, alphabet=None)`
- `WordExtractor(window_size=0.1, window_step=1, numerosity_reduction=True)`
- `BagOfWords(window_size=0.5, word_size=0.5, n_bins=4, strategy='normal', numerosity_reduction=True, window_step=1, threshold_std=0.01, norm_mean=True, norm_std=True, overlapping=True, raise_warning=False, alphabet=None)`

## Signature notes

- The preprocessing classes operate on each time series independently.
- `window_size` and `word_size` may be integers or fractions of the time-series
  length, depending on the class.
- `WordExtractor` expects symbolic, list-like input; do not wrap symbolic rows
  in an object-dtype numpy array unless you have already verified that the
  calling path accepts it.
- `BagOfWords` is the numeric-to-symbolic helper; it extracts windows and then
  discretizes them into words.

## Where the docs still matter

- Use the user-guide docs for long-form explanation of strategy choices
  (`uniform`, `quantile`, `normal`) and for the difference between PAA, SAX,
  DFT, MCB, and SFA.
- Use the root smoke script when you need to verify the installed package on a
  few representative tiny arrays.
