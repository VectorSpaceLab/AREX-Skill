# Preprocessing Troubleshooting

## NaNs or invalid numeric input

**Symptoms**
- `StandardScaler`, `MinMaxScaler`, `PowerTransformer`, or `QuantileTransformer`
  raises a validation error about NaNs or non-finite values.

**Likely causes**
- Missing values were not imputed first.
- The input was not numeric.

**What to do next**
1. Run `InterpolationImputer().fit_transform(X)` before scaling.
2. Keep a clean numeric array for the scaling step.
3. Use the smoke script's `--mode symbolic` output as a known-good example.

## `WordExtractor` / `BagOfWords` input shape issues

**Symptoms**
- A numba typing error or a windowing error appears when transforming symbolic
  input.

**Likely causes**
- `WordExtractor` received an object-dtype array instead of a list-like symbolic
  sequence.
- `window_size` / `word_size` is incompatible with the series length.

**What to do next**
1. Pass a list of lists of symbols to `WordExtractor`.
2. Keep `BagOfWords` on numeric input and let it create the words.
3. Use a tiny list-like test case first, then scale up.

## Binning and symbol-count constraints

**Symptoms**
- `MultipleCoefficientBinning` or `SymbolicFourierApproximation` rejects the
  chosen `n_bins`.
- A discretizer complains about a window or bin setting that is too large.

**Likely causes**
- The number of bins exceeds what the current sample count or timestamp count
  allows.
- The chosen window/word size is larger than the time series itself.

**What to do next**
1. Reduce `n_bins` for very small smoke arrays.
2. Increase the sample count or series length if you need more bins.
3. Check the class signature in `api-reference.md` before retrying.

## Constant or degenerate series

**Symptoms**
- A transform returns a trivial result or refuses to fit.

**Likely causes**
- The input series is constant or nearly constant.
- The toy data is too small for the chosen transform.

**What to do next**
- Use the 2x4 smoke arrays from `scripts/smoke.py`.
- If you need a more realistic example, increase the input diversity before
  raising the bin count or switching to a frequency-domain transform.
