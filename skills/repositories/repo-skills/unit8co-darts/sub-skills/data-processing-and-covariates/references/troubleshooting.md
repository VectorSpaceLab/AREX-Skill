# Data processing and covariate troubleshooting

## Data leakage from preprocessing

**Symptom:** validation/test performance is suspiciously good or preprocessing examples call `fit_transform()` on the whole series.

**Fix:** split first. Fit fittable transformers on train only. Use `transform()` for validation/test and future inference inputs.

```python
train_t = pipe.fit_transform(train)
val_t = pipe.transform(val)
```

## Inverse transform fails or gives wrong scale

**Likely causes:**

- The fitted pipeline object was discarded.
- The forecast has different components from the training target.
- The transform sequence includes a non-invertible stage.

**Fix:** keep the fitted pipeline and inverse-transform only compatible forecasts. If the pipeline contains non-invertible steps such as `MissingValuesFiller`, use `partial=True` to inverse-transform only invertible steps such as `Scaler`. If only the target was scaled, inverse-transform target forecasts, not unrelated covariates.

## Future covariates do not cover `predict(n)`

**Symptom:** Darts raises an error that future covariates are too short or not covering prediction range.

**Fix:**

1. Compute horizon `n` and target `end_time()`.
2. Regenerate calendar/future covariates through at least the required end of prediction.
3. Check `future_covariates.freq == series.freq` or compatible frequency.
4. For multiple target series, validate every target/covariate pair.
5. Route model-specific lag/chunk details to forecasting or torch.

Never append fake target values just to lengthen covariates.

## Past covariate history too short

Past covariates may need enough history for lagged features or input chunks. If a model uses `lags_past_covariates` or an `input_chunk_length`, ensure covariates cover the historical window needed before the first forecast point.

## Transformer column selection errors

Some transformers accept a `columns` argument to restrict transformation to components. Validate component names after `TimeSeries` construction, then pass the exact names. If a user asks to transform only one component, confirm whether the remaining components should be left unchanged or split into separate series.

## Parallel or global-fit confusion

- `global_fit=False` usually fits a fittable transformer separately per series in a sequence.
- `global_fit=True` aggregates fit across multiple series where supported.
- Use `n_jobs` only for safe parallel transformations; it does not change statistical semantics.
