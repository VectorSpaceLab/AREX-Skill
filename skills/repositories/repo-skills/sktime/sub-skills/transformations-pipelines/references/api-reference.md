# Transformations and Pipelines API Reference

Verified signatures:

- `SummaryTransformer(summary_function=('mean', 'std', 'min', 'max'), quantiles=(0.1, 0.25, 0.5, 0.75, 0.9), flatten_transform_index=True)`.
- `Differencer(lags=1, na_handling='fill_zero', memory='all')`.
- `Tabularizer()`.
- `TransformedTargetForecaster(steps)`.
- `ForecastingPipeline(steps)`.

Transformer tags describe input/output scitypes, mtypes, inverse-transform
support, missing-value support, unequal-length behavior, and randomness.
Use `get_tag` on an instance before composing unfamiliar transformers.

Dunder composition is common in sktime: `*` chains transformations, while `+`
forms feature unions where supported. Explicit step names are safer for grid
search because nested parameters use `step__parameter` syntax.
