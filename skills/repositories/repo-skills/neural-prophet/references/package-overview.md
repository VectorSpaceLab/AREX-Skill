# NeuralProphet Package Overview

## Purpose

Read this for a high-level map of the NeuralProphet package before choosing a sub-skill. NeuralProphet is a PyTorch/PyTorch Lightning time-series forecasting framework inspired by Prophet and AR-Net. It combines interpretable components with neural-network training.

## Public entry points

Top-level imports verified for this skill:

```python
from neuralprophet import NeuralProphet, TorchProphet
from neuralprophet import set_log_level, set_random_seed, save, load
from neuralprophet import uncertainty_evaluate
```

The package also exposes dataframe utilities such as `split_df`, `add_quarter_condition`, and `add_weekday_condition`, but most user workflows should start from a `NeuralProphet` instance method.

## Major workflow areas

| Task family | Use |
| --- | --- |
| Core fit/predict | `sub-skills/core-forecasting/SKILL.md` for dataframe validation, `fit`, `make_future_dataframe`, `predict`, and `yhat*` output. |
| Components/exogenous features | `sub-skills/components-and-exogenous/SKILL.md` for trend, seasonality, AR, lagged/future regressors, events, holidays, and multi-series `ID`. |
| Evaluation/uncertainty | `sub-skills/evaluation-and-uncertainty/SKILL.md` for splits, cross-validation, metrics, quantiles, conformal prediction, and uncertainty evaluation. |
| Operations/migration | `sub-skills/operations-and-migration/SKILL.md` for CLI/version, plotting, save/load, logging, seeding, optional extras, accelerators, and `TorchProphet`. |

## Minimal install and import check

For a normal package install:

```bash
python -m pip install neuralprophet
python -c "from neuralprophet import NeuralProphet; print(NeuralProphet)"
```

For this version, practical compatibility findings are:

- Use Python supported by the package metadata (`>=3.9,<3.13`). Python 3.11 was used for verification.
- Use `pandas<3` with this code version because pandas 3 removed an API used during frequency inference.
- If import fails with `pkg_resources`, install `setuptools<81` for the Lightning stack used by this version.
- Optional extras are not required for core forecasting. Install `neuralprophet[plotly-resampler]` only for plotly-resampler support and `neuralprophet[live]` for live loss plotting.

## Data model

A basic training dataframe has:

- `ds`: timestamp column parseable by pandas.
- `y`: numeric target.
- Optional `ID`: series identifier for multi-series/global models.
- Optional extra columns configured as regressors, conditions, or event indicators.

Use the core forecasting validator script before fitting unfamiliar CSV data.
