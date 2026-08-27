# Preprocessing workflows

Use these workflows to make the target scale and exogenous schema explicit
before fitting an ARIMA estimator. Keep all examples deterministic and bounded.

## 1. Choose the smallest adequate transform

| Need | Configuration | Forecast-time input | Main risk |
|---|---|---|---|
| Estimate a power for a positive/shifted target | `BoxCoxEndogTransformer(lmbda=None, lmbda2=shift)` | No future target; Pipeline reverses forecasts | Fit-time MLE still requires strict positivity after shift |
| Apply a fixed log scale | `LogEndogTransformer(lmbda=shift)` | No future target; Pipeline reverses forecasts | Non-positive-after-shift rows need an explicit policy |
| Add fixed-period seasonal regressors | `FourierFeaturizer(m=period, k=harmonics)` | Future terms can be generated from `n_periods` | Fixed periodicity and too many regressors can misrepresent/overfit |
| Add calendar effects | `DateFeaturizer(column_name="date", ...)` | A future DataFrame with typed dates is mandatory | Dates are never inferred |

Fourier features are commonly paired with a non-seasonal ARIMA because the
seasonal signal is represented as exogenous regressors. That is a modeling
choice; do not add both seasonal ARIMA terms and Fourier terms without a reason.

## 2. Configure a safe target transform

1. Inspect the training minimum and decide whether the additive shift is part
   of the data contract. Choose `lmbda2` (Box-Cox) or public `lmbda` (log) so
   expected training values are strictly positive after the shift.
2. For automatic Box-Cox lambda estimation, keep `lmbda=None` and satisfy
   strict positivity before `fit`. `neg_action` only runs in `transform` and
   does not repair MLE input.
3. The source-supported `neg_action` values are exactly `"raise"`, `"warn"`,
   and `"ignore"`. Prefer `"raise"` for an auditable workflow. Use `"warn"`
   or `"ignore"` only when replacing non-positive rows by `floor` is
   intentional, and record that those rows cannot be exactly
   inverse-transformed. Do not configure `"clip"`; although unknown strings
   currently fall through to silent replacement, that is not a supported API.
4. Verify the tuple and inverse contract before fitting the model:

   ```python
   trans = BoxCoxEndogTransformer(lmbda=0.0)
   y_model, X_model = trans.fit_transform(y_train, X_train)
   y_back, X_back = trans.inverse_transform(y_model, X_model)
   assert y_model.shape == y_train.shape
   # For strictly positive y_train, y_back matches y_train to tolerance.
   ```

5. For a pure log, use `LogEndogTransformer`; its public shift is clone-safe
   even though the implementation stores it internally as `lmbda2`.

## 3. Compose target and exogenous stages

Every `fit_transform`/`transform` stage returns the explicit tuple
`(y_transformed, X_transformed)`, not just a transformed target or feature
matrix. Pass both tuple items through every stage. A stable composition is:

```python
pipe = Pipeline([
    ("log", LogEndogTransformer(lmbda=1.0)),
    ("fourier", FourierFeaturizer(m=12, k=3)),
    ("arima", ARIMA(order=(1, 0, 0), seasonal_order=(0, 0, 0, 0))),
])
pipe.fit(y_train)
forecast = pipe.predict(n_periods=6)  # original target scale by default
```

The conceptual flow is:

```text
(y, X)
  -> Log/Box-Cox     (transformed y, same X)
  -> Fourier/Date    (same y, augmented X)
  -> ARIMA/AutoARIMA (fit on both outputs)
```

Every arrow carries the full `(y_current, X_current)` tuple; never discard the
pass-through item. Pipeline preserves the listed stage order and clones each
intermediate transformer when fitting, while using the supplied final
`ARIMA`/`AutoARIMA` estimator. Target-stage order controls nested inverse
transformations (inverse runs in reverse order). Exogenous-stage order controls
the order in which feature blocks are appended. Prefer a stable explicit order
even though Pipeline records and later reselects DataFrame columns by name.

## 4. Use Fourier safely

- Pick a positive integer `m` equal to observations per seasonal cycle, not the
  forecast horizon. Pick integer `k` with `1 <= k <= m // 2`; start small.
- Fit with `y_train` so the featurizer records the training length, then call
  `transform(None, n_periods=h)` for an `h`-row future block.
- If there are known exogenous variables, call
  `transform(None, X_future, n_periods=len(X_future))`; Fourier columns append
  to the right of those variables.
- In Pipeline, omit a manual `fourier__n_periods` unless it equals the requested
  horizon. Pipeline supplies the horizon and rejects a conflicting override.
- Check generated names and row count before passing the matrix to ARIMA.

## 5. Use DateFeaturizer with an explicit future frame

```python
train_frame = train_frame.copy()
future_frame = future_frame.copy()
train_frame["date"] = pd.to_datetime(train_frame["date"])
future_frame["date"] = pd.to_datetime(future_frame["date"])

pipe = Pipeline([
    ("dates", DateFeaturizer(column_name="date")),
    ("arima", ARIMA(order=(0, 0, 0))),
])
pipe.fit(y_train, X=train_frame)
X_future = pipe.transform(X=future_frame)
forecast = pipe.predict(X=future_frame)
```

The configured date column must be present and datetime-typed in both frames.
Keep every other covariate used during fit in the future frame. The date source
is consumed and replaced by generated columns. `len(future_frame)` determines
the forecast horizon when supplied to `Pipeline.predict`.

## 6. Inspect pipeline output before forecasting

Use `Pipeline.transform` as a schema gate:

```python
X_future_transformed = pipe.transform(n_periods=6)       # Fourier-only
# or: pipe.transform(X=future_frame)                     # date/user X
assert len(X_future_transformed) == 6
assert list(X_future_transformed.columns) == pipe.x_feats_
```

For a numpy exogenous matrix, inspect shape rather than `x_feats_`; DataFrame
column alignment is only available when the transformed fit output is a
DataFrame. If `X` is passed to `Pipeline.predict`, its row count becomes the
forecast horizon. If the final model was fit with exogenous features, do not
call `predict` or `update` without compatible future/observed `X`.

## 7. Understand the inverse boundary

The final model sees transformed `y` when an endogenous stage is present.
With the default `inverse_transform=True`, Pipeline reverses only endogenous
stages after forecasting, including both bounds of confidence intervals. Set
`inverse_transform=False` only when model-scale diagnostics are intended. A
floor-replaced training row remains lossy regardless of this flag.
