# Distribution Troubleshooting

## Shape and dtype errors

- Use 2D data `(n, d)` for `fit`, `summarize`, `log_probability`, and `probability`.
- Use integer tensors for categorical-style distributions; continuous distributions should use floating point values.
- If an initialized distribution has dimension `d`, later data must have the same second dimension.
- Keep `check_data=True` while debugging so pomegranate reports validation problems early.

## Probability parameter errors

- Probability vectors must be nonnegative and sum to 1 where the constructor requires a probability simplex.
- `Categorical` probabilities for a univariate feature are shaped like `[[p0, p1, ...]]` because pomegranate distributions are multivariate by design.
- `ConditionalCategorical` probability tables must align parent dimensions before the child-category axis; mismatched table shape is the most common failure.
- `JointCategorical` factors should represent a normalized joint table over all variables in the factor.

## Range checks

| Distribution | Common invalid values |
| --- | --- |
| `Bernoulli` | Values outside `{0, 1}`. |
| `Categorical` / `ConditionalCategorical` | Negative categories or category ids above the table size. |
| `Exponential`, `Gamma`, `Poisson` | Negative observations or nonpositive rate/scale parameters. |
| `Uniform` | `mins` greater than `maxs`, values outside bounds when scoring. |
| `Normal` | Negative covariance/variance entries or singular full covariance. |

## Missing values

If missing values do not work:

1. Build `torch.masked.MaskedTensor(data, mask=mask)` where `mask=True` means observed.
2. Use diagonal/spherical normal or distributions with tested masked support before trying more complex cases.
3. Avoid missing-value claims for Bernoulli, categorical distributions, full-covariance `Normal`, and `Uniform` unless the exact path is locally verified.
4. If a masked result exposes `_masked_data`, convert only after preserving the mask semantics.

## Fitting and updating surprises

- `fit` usually calls `summarize` and then `from_summaries`; repeated `fit` calls reset/update according to model rules.
- `summarize` accumulates statistics, so calling it multiple times before `from_summaries` is intentional for chunked learning.
- `frozen=True` prevents updates; call `unfreeze()` or construct a non-frozen distribution before expecting parameters to change.
- `inertia=1.0` effectively keeps old parameters; use lower inertia for actual updates.

## `ZeroInflated` caveat

`ZeroInflated` wraps a base distribution and performs EM-style fitting for excess-zero data. Before using it as a drop-in distribution, verify that the exact method you need is implemented for the installed version. If a scoring path raises `NotImplementedError`, use `GeneralMixtureModel` with an explicit `DiracDelta`/base-distribution design or avoid the scoring call.
