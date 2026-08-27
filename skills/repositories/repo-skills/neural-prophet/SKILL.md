---
name: neural-prophet
description: "Use NeuralProphet for interpretable time-series forecasting with
  fit/predict, components, uncertainty, plotting, save/load, and Prophet
  migration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# NeuralProphet repo skill

Use this skill when a task involves the Python package `neuralprophet` / NeuralProphet: Prophet-like time-series forecasting, `ds`/`y` dataframes, forecast horizons, trend/seasonality/autoregression/regressor/event components, global multi-series models, uncertainty intervals, plotting, serialization, or `TorchProphet` migration.

## First checks

Install from PyPI for normal use:

```bash
python -m pip install neuralprophet
python -c "from neuralprophet import NeuralProphet; print(NeuralProphet)"
```

For this version, prefer Python supported by the package metadata (`>=3.9,<3.13`). If imports or fitting fail, read [references/troubleshooting.md](references/troubleshooting.md); known practical compatibility fixes include `pandas<3` and `setuptools<81` for the verified source snapshot.

Run the bundled diagnostic when the user's environment is uncertain:

```bash
python scripts/check_neuralprophet_install.py
```

Use `--check-cuda` only when the user explicitly needs CUDA verification. Core workflows are CPU-capable.

## Route map

| User intent | Load |
| --- | --- |
| Quickstart forecasting, dataframe validation, `fit`, `predict`, future periods, `yhat*` columns | `sub-skills/core-forecasting/SKILL.md` |
| Trend, changepoints, seasonality, autoregression, lagged/future regressors, events, holidays, global/local multi-series modeling | `sub-skills/components-and-exogenous/SKILL.md` |
| Train/validation/test splits, cross-validation, metrics, quantile regression, conformal prediction, uncertainty evaluation | `sub-skills/evaluation-and-uncertainty/SKILL.md` |
| CLI/version, logging, seeding, plotting backends, optional extras, save/load, accelerators, TorchProphet/Prophet migration | `sub-skills/operations-and-migration/SKILL.md` |

## Shared references

- [package-overview.md](references/package-overview.md) gives the package purpose, top-level imports, data model, install notes, and workflow map.
- [troubleshooting.md](references/troubleshooting.md) covers cross-cutting import, dependency, data, optional-extra, and backend failures.
- [repo-provenance.md](references/repo-provenance.md) records the source snapshot used to build this skill; read it before deciding whether to refresh the skill for a changed checkout.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is structured router metadata for managed import tooling.

## Common package pattern

```python
import pandas as pd
from neuralprophet import NeuralProphet, set_log_level

set_log_level("ERROR")
df = pd.DataFrame({"ds": timestamps, "y": values})
model = NeuralProphet(epochs=10, accelerator="cpu")
metrics = model.fit(df, freq="D")
future = model.make_future_dataframe(df, periods=30, n_historic_predictions=True)
forecast = model.predict(future)
```

Add components before `fit`, validate all required columns before prediction, and keep explicit frequency strings for irregular or calendar-sensitive data.

## Do not use this skill when

- The task is only generic PyTorch Lightning training internals with no NeuralProphet forecasting API.
- The task is general repository maintenance or contribution work rather than using the package.
- The user needs another forecasting library with incompatible data schema or model APIs.
- The task requires benchmark-scale training, external tutorial downloads, credentials, services, or hardware-specific claims that have not been separately authorized and verified.
