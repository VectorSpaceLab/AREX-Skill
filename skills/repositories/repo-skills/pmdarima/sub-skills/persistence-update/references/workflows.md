# Persistence and update workflows

These workflows assume a trusted producer, trusted data, and an environment
whose package versions have been recorded. They do not make pickle safe for
untrusted input.

## 1. Establish an artifact contract

Before fitting or loading, write a manifest beside the model artifact. At
minimum record:

- `pmdarima.__version__`, Python version, statsmodels, NumPy, SciPy,
  scikit-learn, pandas, and joblib versions;
- model class, `order`, `seasonal_order`, trend/intercept settings, and each
  fitted transformer class/configuration;
- whether `y` is raw scale at the public boundary, fitted `x_feats_`, external
  exogenous column names/order/width, and whether Fourier or date features are
  generated internally;
- training row count/range, the next expected timestamp or position, accepted
  update batch size/order, forecast horizon, artifact checksum, and creation
  and update timestamps.

Capture the manifest from the environment that creates the artifact, not from a
later consumer. Compare it at load time and preserve an explicit compatibility
review decision when versions differ.

## 2. Fit, predict, and validate a complete `Pipeline`

1. Keep `y` finite, one-dimensional, and in temporal order. If `X` is used,
   align one row with every `y` observation and keep names and meanings stable.
2. Build an ordered pipeline with pmdarima transformer stages first and
   `ARIMA`/`AutoARIMA` last. Use a fixed Box-Cox lambda/offset when the
   transformation contract is known; otherwise verify fitted `lam1_` and
   `lam2_` before promoting the model.
3. Call `pipeline.fit(y, X=training_X, **stage_kwargs)`. Inspect fitted
   `pipeline.steps_` and the final estimator rather than the original
   transformer objects in `pipeline.steps`.
4. Before persistence, call a short forecast and, when useful, an interval
   forecast. Assert `forecast.shape == (h,)` and interval shape `(h, 2)`.
   Provide exactly `h` future `X` rows with the fitted width. For a Fourier
   stage, let the pipeline set the horizon or ensure any routed horizon agrees.
5. Preserve the raw-scale boundary: `pipeline.predict` inverse-transforms
   endogenous stages by default, while `inverse_transform=False` deliberately
   returns the transformed scale.

## 3. Observe, update, and forecast

Use this only for a genuinely new, ordered batch while the model order,
feature schema, and transformer assumptions remain valid:

```python
before = pipeline.predict(n_periods=h, X=future_X)
returned = pipeline.update(new_y_raw, X=new_X, maxiter=bounded_iterations)
assert returned is pipeline.steps_[-1][1]  # pmdarima 2.1.1 return contract
after = pipeline.predict(n_periods=h, X=next_future_X)
```

The batch must not overlap or rewrite fitted history. `new_y_raw` is raw scale
when an endogenous transformer is present. `new_X` has one row per new value
and the same feature width/semantics as training `X`; `next_future_X` has one
row per next forecast period.

`Pipeline.update` runs intermediate stages first. Updatable stages such as
`FourierFeaturizer` generate features for the batch and advance their position;
other stages apply their fitted transform without relearning. The final ARIMA
then performs a local update seeded from its old parameters. Check state
advancement, finite output, optimizer warnings, and forecast shapes. If a
transformer or optimizer fails after mutating the object, discard that
in-memory instance and reload the last known-good artifact; do not persist it.

After a successful update, create a new versioned artifact and manifest. Keep
the previous artifact until the new one passes reload and smoke-forecast
validation.

## 4. Trusted pickle round-trip and atomic promotion

1. Use `pickle` or `joblib` only for an artifact produced by a trusted,
   compatible environment. Validate provenance/checksum before loading. Never
   accept an upload or arbitrary path as a default input.
2. Write to a temporary file in the **same directory/filesystem** as the
   target, using a unique name. Flush and `fsync` the file when durability
   matters.
3. Load only the temporary file created by this process, capture
   `UserWarning`s, check the class/fitted state and manifest, and run a known
   forecast with known-shape `X`. Compare against the pre-save smoke result
   where deterministic equality is expected.
4. Write or validate the manifest/checksum. After all checks pass, atomically
   replace the target with `os.replace(temp_path, target_path)`. Do not delete
   the old target first. If any check fails, remove only the temporary file and
   retain the old last-known-good artifact.
5. On the consumer side, reload the promoted target in a clean process and run
   the same smoke check before serving forecasts or applying updates.

Atomic replacement prevents readers from seeing a partially written pickle;
it does not authenticate the artifact and does not make deserialization safe.
A sidecar checksum detects corruption/tampering but cannot establish trust.

The bundled [`pipeline_roundtrip.py`](../scripts/pipeline_roundtrip.py) shows a
small trusted self-round-trip. It stages and validates a pickle created by the
script before promoting it, and never accepts an input artifact path.
[`update_forecast.py`](../scripts/update_forecast.py) adds the update/state-
advancement case.

## 5. Decide between update and refit

Choose `update` when all of the following are true:

- observations are new, ordered, and complete;
- target and external-exog schemas and feature meanings are unchanged;
- Box-Cox/log domains and fitted transformer assumptions still hold;
- the existing order/seasonal structure remains defensible;
- the batch is bounded and local parameter adjustment is sufficient; and
- convergence/warnings and validation metrics remain acceptable.

Choose a fresh `fit` (and possibly a new `auto_arima` search) when there is
material drift, corrected historical data, a changed schema or feature
meaning, a changed seasonal period, a new transformation domain, repeated or
large accumulated updates, missing fitted state, optimizer instability, or a
need to compare orders. A refit should start from a retained trusted recipe and
explicit training boundary; increasing `maxiter` on `update` is not a refit.

## 6. Exogenous and transformer alignment checklist

- Check `len(y) == len(X)` at fit and update boundaries.
- Check `X.shape[1]` and DataFrame column meanings against the manifest.
- For direct ARIMA prediction, require `X.shape[0] == h`; for direct update,
  require `X.shape[0] == len(new_y)`. For a pipeline, do not rely on its
  effective-horizon adjustment when `X` length differs from requested `h`.
- Pass raw `new_y` once to a pipeline with Box-Cox/log stages. Do not manually
  transform it first.
- Confirm `pipeline.steps_` transformer state after fit and after update; for
  Fourier, `n_` should increase by the number of observed rows.
- Refit if a transformer must relearn parameters, a feature is renamed or
  redefined, or a new batch violates the fitted domain.
