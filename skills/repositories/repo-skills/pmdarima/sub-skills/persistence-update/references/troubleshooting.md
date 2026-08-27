# Persistence and update troubleshooting

Treat the symptom and the recovery separately. Do not promote an artifact just
because it can be unpickled; it must load in the intended trusted environment,
retain fitted state, and pass a known-shape forecast/update smoke test.

## Installation, import, and compiled-extension failures

- **`ModuleNotFoundError: No module named pmdarima` or dependency import
  errors:** activate the intended environment, inspect the installed pmdarima
  and dependency versions, and install pmdarima with a compatible
  Python/platform build. Avoid assuming that a source checkout and a
  separately installed wheel are interchangeable.
- **`pmdarima.__check_build` / compiled module missing, or an import fails
  while loading `_arima`/Fourier extensions:** the package was not built for
  this interpreter or the build artifact is incomplete. Reinstall/rebuild in a
  clean compatible environment and run a simple import plus forecast before
  touching persisted artifacts. Do not patch a pickle to bypass the import.
- **Local checkout shadows the intended installation:** verify
  `pmdarima.__file__` and `pmdarima.__version__` from the actual consumer
  process. Run the check from a neutral working directory or install the
  intended build; record the environment that produced the artifact.

## Trust and persistence failures

- **Untrusted pickle/joblib:** do not load it. Python deserialization can
  execute arbitrary code; a read-only directory, checksum, extension, or
  “test-only” label is not a security boundary. Obtain a trusted artifact or
  retrain from source data and a reviewed recipe.
- **Corrupted or truncated artifact:** retain the last known-good version and
  retrain or restore it. Use a temporary same-directory write followed by
  validation and atomic replacement; never delete the old artifact before the
  replacement is known-good.
- **Missing fitted state (`NotFittedError`, missing `steps_`, `arima_res_`,
  `lam1_`, or Fourier `n_`):** the object was never fit, the wrong/original
  transformer was inspected, or the artifact is incomplete. Fit the complete
  pipeline and inspect fitted `pipeline.steps_`; for a damaged artifact,
  reload the last known-good file or rebuild from the recipe. Do not call
  `predict` or `update` on an unfitted object.

## Version, ABI, and warning failures

- **pmdarima version-mismatch `UserWarning` on unpickle:** fitted ARIMA state
  stores `pkg_version_`; `__setstate__` warns when it differs from the current
  version, and also warns for an older fitted state with no version attribute.
  Capture the warning, compare the complete manifest, run a forecast and (if
  needed) update smoke test in an isolated compatible environment, and prefer
  retraining when compatibility is not explicitly accepted. Never suppress
  the warning as a production approval.
- **Dependency ABI/layout mismatch:** missing classes, statsmodels result
  errors, NumPy/SciPy binary-ABI errors, Python ABI errors, or failures that
  occur before the pmdarima warning indicate an incompatible runtime. Recreate
  the producer dependency set or retrain from a trusted recipe. Do not edit
  pickle bytes or blindly upgrade one dependency in place.
- **Round-trip succeeds but forecasts differ:** compare pmdarima and all
  recorded dependency versions, fitted transformer parameters, exogenous names
  and order, model state, and data precision. Re-run in a clean process with a
  fixed smoke input; same-environment success does not establish cross-version
  equivalence.

## Exogenous row/width and pipeline alignment failures

- **“must also be provided for predicting or updating observations”:** the
  fitted ARIMA used exogenous variables. Pass `X` for every corresponding
  forecast/update. For direct prediction, rows equal `n_periods`; for direct
  update, rows equal `len(new_y)`.
- **X row mismatch:** check `len(y) == len(X)` at fit/update and
  `len(future_X) == h` at forecast. A pipeline can derive its effective horizon
  from `len(X)` when it differs from the requested `n_periods`, so do not rely
  on that adjustment; pass the intended row count explicitly.
- **X width or column-order mismatch:** preserve the fitted DataFrame names,
  order, and meanings. `Pipeline.x_feats_` reorders known columns but cannot
  supply missing columns, remove duplicate semantic features, or repair a
  changed meaning. For a direct ARIMA, fix `X.shape[1]` to the fitted width.
- **Fourier horizon mismatch:** a manually routed Fourier
  `stage__n_periods` must agree with the requested horizon. Remove the manual
  value and let `Pipeline.predict` provide it, or set it correctly.
  `FourierFeaturizer.update_and_transform` requires a non-`None` `y` and
  advances `n_` only after generating the new rows.

## Transformer-domain and update failures

- **Box-Cox/log update raises `ValueError: Negative or zero values present in
  y`:** the new raw values plus the fitted `lmbda2` contain a non-positive
  value. Validate/quarantine the batch; do not change the offset for only the
  new rows and do not pass values that were already transformed. Refit with a
  reviewed transformation/domain over the complete data when appropriate.
  `neg_action="warn"` or `"ignore"` truncates to `floor` and sacrifices exact
  inverse-transformability; it is not a silent repair.
- **Manual double transformation or wrong scale:** pipeline update expects
  raw `y` and applies the fitted endogenous transformer. Passing Box-Cox/log
  output as if it were raw data can distort or invalidate the update. Keep the
  public scale contract in the manifest.
- **Transformer state did not advance:** only a stage implementing
  `update_and_transform` learns/advances during `Pipeline.update`; ordinary
  stages only transform. Inspect fitted `steps_` and expected state such as
  Fourier `n_`. Refit if the ordinary transformer's learned statistics need to
  change.

## Optimizer and partial-update failures

- **`maxiter` is too small or update does not converge:** with `maxiter=None`,
  ARIMA uses `max(5, n_new // 10)`; an explicit value bounds the local
  optimization seeded from old parameters. Increase it only within a bounded
  retry policy and inspect convergence/optimizer warnings. `maxiter` does not
  perform order search or replace a clean refit.
- **Update changes forecasts unexpectedly:** appended observations alter the
  model state, so exact equality is not expected. Check raw values, ordering,
  transformer state, exogenous alignment, warnings, and validation error. If
  the change is implausible or drift is material, reload the old artifact and
  refit instead.
- **Failure after a transformer or optimizer partially mutates the object:**
  treat that object as non-authoritative. Do not pickle it. Reload the last
  known-good artifact, reproduce the failure on a copy, correct the data/schema
  or choose a full refit, then validate before promotion.
