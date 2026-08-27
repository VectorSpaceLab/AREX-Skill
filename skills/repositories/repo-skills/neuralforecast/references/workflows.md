# Workflows

## Purpose

Read this when you want the shortest end-to-end recipe for forecasting,
validation, prediction intervals, save/load, simulation, or explainability.

## 1. Quickstart forecast

```python
from neuralforecast import NeuralForecast
from neuralforecast.models import NHITS
from neuralforecast.utils import AirPassengersDF

nf = NeuralForecast(
    models=[NHITS(h=12, input_size=24, max_steps=1, enable_progress_bar=False)],
    freq="ME",
)
nf.fit(AirPassengersDF)
fcst = nf.predict()
```

Use this when you only need a single model and a fast proof that the package is
installed correctly.

## 2. Exogenous variables

Use `hist_exog_list`, `futr_exog_list`, and `stat_exog_list` on the model, then
pass `static_df` and `futr_df` to `fit` / `predict` when the model needs them.

```python
from neuralforecast import NeuralForecast
from neuralforecast.models import NHITS
from neuralforecast.utils import AirPassengersPanel, AirPassengersStatic

model = NHITS(h=12, input_size=24, hist_exog_list=["trend"], futr_exog_list=["trend"])
nf = NeuralForecast(models=[model], freq="M")
nf.fit(AirPassengersPanel, static_df=AirPassengersStatic)
fcst = nf.predict(futr_df=AirPassengersPanel.tail(24))
```

## 3. Cross-validation and intervals

```python
from neuralforecast import NeuralForecast
from neuralforecast.models import NHITS
from neuralforecast.utils import AirPassengersDF, PredictionIntervals

model = NHITS(h=12, input_size=24, max_steps=2, val_check_steps=1)
nf = NeuralForecast(models=[model], freq="ME")
nf.fit(
    AirPassengersDF,
    val_size=12,
    prediction_intervals=PredictionIntervals(n_windows=2),
)
cv = nf.cross_validation(AirPassengersDF, n_windows=2, step_size=1)
preds = nf.predict(level=[80, 90])
```

Use this when a user asks for backtesting, interval columns, or a validation
window for early stopping.

## 4. Predict in-sample

```python
insample = nf.predict_insample(step_size=1)
```

Use this after a fit or cross-validation when the user wants fitted values or a
training-window diagnostic.

## 5. Save and load

```python
path = "/tmp/neuralforecast-save"
nf.save(path, overwrite=True)
restored = NeuralForecast.load(path)
restored_preds = restored.predict()
```

Use this for portability or when the user needs to reload a fitted model in a
later session.

## 6. Simulation and explanation

- `simulate(...)` generates forecast paths using the fitted model state.
- `explain(...)` provides supported model explanations and feature attribution
  style outputs.
- Both depend on the underlying model family and the data layout already being
  correct.

## 7. Hierarchical forecasts

`HINT(h, S, model, reconciliation)` wraps a base model and a summing matrix.
Use it when the user explicitly needs reconciliation across a hierarchy.

## Safe bundled checks

- `scripts/core_smoke.py` for a tiny fit/predict run.
- `scripts/check_serialization.py` for a small save/load round-trip.
- `scripts/check_losses.py` if the workflow depends on probabilistic outputs.

## Read next

- `data-formats.md` for panel layout and exogenous rules.
- `losses-reference.md` for quantile and interval workflows.
- `troubleshooting.md` when a workflow fails with a predictable error.
