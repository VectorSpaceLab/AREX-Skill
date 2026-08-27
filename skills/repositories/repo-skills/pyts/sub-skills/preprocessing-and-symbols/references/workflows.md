# Preprocessing and Symbolic Workflows

## When to read

Read this when the task is to clean a time series, reduce its length, discretize
it, or build a symbolic representation before modeling.

## Common recipes

### 1. Impute then scale

Use this when the series contains missing values or wildly different scales.

```python
from pyts.preprocessing import InterpolationImputer, StandardScaler
X_clean = InterpolationImputer().fit_transform(X)
X_scaled = StandardScaler().fit_transform(X_clean)
```

### 2. Downsample with PAA, then discretize with SAX

Use this when you want a symbolic representation that preserves coarse shape.

```python
from pyts.approximation import PiecewiseAggregateApproximation, SymbolicAggregateApproximation
X_paa = PiecewiseAggregateApproximation(window_size=2).fit_transform(X)
X_sax = SymbolicAggregateApproximation(n_bins=3, strategy='uniform').fit_transform(X_paa)
```

### 3. Build words from symbolic input

Use `WordExtractor` when the input is already symbolic, and `BagOfWords` when
it is still numeric.

```python
from pyts.bag_of_words import WordExtractor, BagOfWords
words = WordExtractor(window_size=2).fit_transform([['a', 'a', 'b', 'c']])
bow = BagOfWords(window_size=2, word_size=2, n_bins=3, strategy='uniform').fit_transform(X)
```

### 4. Fourier-based symbolic transforms

Use the Fourier-based transforms when the signal is better described in the
frequency domain than in the raw time domain.

```python
from pyts.approximation import DiscreteFourierTransform, MultipleCoefficientBinning, SymbolicFourierApproximation
X_dft = DiscreteFourierTransform(n_coefs=2).fit_transform(X)
X_mcb = MultipleCoefficientBinning(n_bins=2).fit_transform(X_dft)
X_sfa = SymbolicFourierApproximation(n_coefs=2, n_bins=2).fit_transform(X)
```

## Verified smoke behavior

The bundled smoke script currently confirms these tiny cases:

- `StandardScaler`, `MinMaxScaler`, `MaxAbsScaler`, `RobustScaler`,
  `PowerTransformer`, and `QuantileTransformer` on a 2x4 array.
- `InterpolationImputer` on a tiny array containing `NaN`.
- `KBinsDiscretizer` on a 2x4 array.
- `PiecewiseAggregateApproximation` and `SymbolicAggregateApproximation` on a
  2x4 array.
- `DiscreteFourierTransform` and `BagOfWords` on tiny arrays.
- `WordExtractor` on a symbolic Python list of lists.

## Practical guidance

- Use `fit_transform` when you want a one-liner for a tiny smoke check.
- Keep symbolic input list-like for `WordExtractor`; an object-dtype array can
  trigger numba typing issues.
- Prefer small, explicit toy arrays when you need deterministic debugging.
- Keep preprocessing here; route model-building or image transforms to other
  sub-skills.
