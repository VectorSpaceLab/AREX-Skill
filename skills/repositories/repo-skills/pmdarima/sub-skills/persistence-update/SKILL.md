---
name: persistence-update
description: "Persist, reload, update, and forecast pmdarima ARIMA models and
  pipelines safely, including transformer state, exogenous alignment, and
  version compatibility."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Persistence and update

Use this route when a fitted `ARIMA`, `AutoARIMA`, or
`pmdarima.pipeline.Pipeline` must be serialized, reloaded, refreshed with new
observations, or forecast after a refresh. Keep the artifact coupled to the
producer environment and treat pickle/joblib deserialization as a trusted-code
operation.

## Route

1. Establish the fitted object's class and fitted state, pmdarima/Python and
dependency versions, transformer configuration, exogenous schema, training
row count/range, forecast-horizon contract, and artifact checksum. Read [the
API reference](references/api-reference.md) for source-level contracts.
2. Fit the complete pipeline, including endogenous and exogenous transformers,
and smoke-test `predict` before persistence. Keep `y` and every `X` row in
temporal alignment; for forecasts, provide one future `X` row per period and
the same feature width.
3. Persist only a trusted object with `pickle` or `joblib`. Stage writes in a
trusted temporary path on the same filesystem, validate a same-environment
reload and known-shape forecast, then atomically replace the artifact of
record. Never load an untrusted or arbitrary path.
4. For a small, ordered batch whose schema and model structure remain valid,
pass raw new observations to `Pipeline.update(y, X=..., maxiter=...)` or
`ARIMA.update(...)`. `Pipeline.update` mutates the fitted pipeline but returns
the final estimator in pmdarima 2.1.1. Preserve fitted transformer semantics:
updatable stages advance, ordinary stages only transform, and the final ARIMA
receives aligned transformed data.
5. Prefer a clean refit (and possibly order search) after drift, corrected
history, schema/feature meaning changes, changed transformation domains or
seasonality, repeated updates, or non-convergence. An update is not a new
order search or a substitute for validation.

Read [workflows](references/workflows.md) for fit/predict/update, trusted
round-trip, metadata, atomic replacement, refit decisions, and alignment.
Read [troubleshooting](references/troubleshooting.md) before recovering load,
exogenous, transformer, or optimizer failures.

## Bundled checks

- [`scripts/pipeline_roundtrip.py`](scripts/pipeline_roundtrip.py) fits a
deterministic small Box-Cox pipeline, records a compact version/schema manifest,
stages and validates its own temporary artifact, atomically promotes it,
reloads it, and asserts forecast shape and equality.
- [`scripts/update_forecast.py`](scripts/update_forecast.py) fits a small
Box-Cox-plus-Fourier pipeline, updates it with raw observations using bounded
`maxiter`, asserts Fourier state advancement and forecast shape, then validates
and round-trips the artifact it created.

Both scripts accept `--help`, work from arbitrary current directories, use
local deterministic data, default to temporary paths, and never accept an
input artifact path.

## Provenance boundary

This route describes pmdarima 2.1.1 source behavior at commit
`4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9`. Verify the installed package and
dependency versions before applying any persisted artifact; an inspection
environment can legitimately report a different development version.

## Local references

- [API reference](references/api-reference.md) — signatures, state, shape,
  transformer, and persistence contracts.
- [Workflows](references/workflows.md) — bounded operational sequences and the
  atomic promotion policy.
- [Troubleshooting](references/troubleshooting.md) — installation, trust,
  compatibility, alignment, domain, and update recovery.
