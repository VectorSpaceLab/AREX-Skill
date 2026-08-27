# Maintainer testing for custom components

Use focused checks before running broad suites. The package test configuration enables coverage by default, so targeted `pytest` selections are much cheaper than a whole-repository run.

## 1) Dependency stance

Start from the minimum environment needed for the component.

- Core custom metrics and small v1/v2 model smoke tests normally need only the package's core dependencies plus `pytest` if you run tests.
- `MQF2DistributionLoss` requires the `cpflows` optional extra; do not select MQF2 loss cases unless that dependency is installed.
- Tuning flows need `optuna`, `optuna-integration`, and sometimes `statsmodels`.
- Plotting or docs work can require `matplotlib` or documentation extras, but those are not needed for a metric/model/package-wrapper smoke test.
- Avoid `all_extras` or broad `dev` installation unless the task actually needs all developer hooks, docs/notebook tooling, or optional estimators.

## 2) Syntax and import checks

Run these before estimator tests:

```bash
python -m py_compile path/to/new_metric.py path/to/new_model.py path/to/_my_model_pkg.py
python - <<'PY'
from pytorch_forecasting import TimeSeriesDataSet, QuantileLoss, SMAPE
from pytorch_forecasting.models.base import BaseModel
print("core imports ok")
PY
```

For a package wrapper, verify the registry can discover it:

```bash
python - <<'PY'
from pytorch_forecasting._registry import all_objects
rows = all_objects(
    object_types="forecaster_pytorch_v1",
    return_tags=["info:name", "python_dependencies"],
)
print([row[0] for row in rows if "MyModel" in row[0]])
PY
```

For a metric wrapper:

```bash
python - <<'PY'
from pytorch_forecasting._registry import all_objects
rows = all_objects(object_types="metric", return_tags=["metric_type", "requires:data_type"])
print([row[0] for row in rows if "MyMetric" in row[0]])
PY
```

## 3) Tiny manual model smoke

For a v1 model, use a tiny CPU `TimeSeriesDataSet`, a small batch size, and Lightning `fast_dev_run=True` before running estimator tests.

```python
import numpy as np
import pandas as pd
from lightning.pytorch import Trainer
from pytorch_forecasting import TimeSeriesDataSet

frame = pd.DataFrame(
    {
        "series": np.repeat(["a", "b"], 12),
        "time_idx": list(range(12)) * 2,
        "target": np.sin(np.arange(24) / 3.0),
    }
)

dataset = TimeSeriesDataSet(
    frame,
    time_idx="time_idx",
    target="target",
    group_ids=["series"],
    max_encoder_length=6,
    max_prediction_length=2,
    time_varying_unknown_reals=["target"],
)
loader = dataset.to_dataloader(train=True, batch_size=2, num_workers=0)
model = MyModel.from_dataset(dataset, hidden_size=4, log_interval=1)
Trainer(fast_dev_run=True, accelerator="cpu", logger=False, enable_checkpointing=False).fit(
    model,
    train_dataloaders=loader,
    val_dataloaders=loader,
)
```

## 4) Focused pytest selections

Use `-k MyModel` or `-k MyMetric` to avoid running all estimators/metrics.

### v1 model/package checks

```bash
python -m pytest pytorch_forecasting/tests/test_all_estimators.py::TestAllPtForecasters::test_pkg_linkage -q -k MyModel
python -m pytest pytorch_forecasting/tests/test_all_estimators.py::TestAllPtForecasters::test_integration -q -k MyModel
```

`test_pkg_linkage` catches `_pkg()` imports, class naming, and `info:name` mismatches. `test_integration` catches `from_dataset()`, training, checkpoint load, `predict(mode="raw")`, and raw prediction shape issues.

### v2 model/package checks

```bash
python -m pytest pytorch_forecasting/tests/test_all_v2/test_all_estimators_v2.py::TestAllPtForecastersV2::test_pkg_linkage -q -k MyModel
python -m pytest pytorch_forecasting/tests/test_all_v2/test_all_estimators_v2.py::TestAllPtForecastersV2::test_integration -q -k MyModel
python -m pytest pytorch_forecasting/tests/test_all_v2/test_all_estimators_v2.py::TestAllPtForecastersV2::test_predict_modes -q -k MyModel
```

`test_predict_modes` is important for v2 because package-level `predict()` expects `raw`, `quantiles`, and `prediction` modes to return consistent shapes.

### Metric checks

```bash
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_metric_type -q -k MyMetric
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_metric_update_and_compute -q -k MyMetric
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_to_prediction -q -k MyMetric
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_to_quantiles -q -k MyMetric
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_loss_method -q -k MyMetric
```

For distribution or quantile metrics, add the composite/reduction checks:

```bash
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_composite_and_weighted_metrics -q -k MyMetric
python -m pytest pytorch_forecasting/metrics/tests/test_all_metrics.py::TestAllPtMetrics::test_reduction_modes -q -k MyMetric
```

## 5) Ruff, formatting, mypy, and pre-commit

The project uses 88-character ruff formatting and targets Python 3.10+.

Focused commands:

```bash
python -m ruff check path/to/new_component.py --fix
python -m ruff format path/to/new_component.py
python -m mypy path/to/new_component.py
```

When pre-commit is installed, prefer file-scoped runs:

```bash
python -m pre_commit run --files path/to/new_component.py path/to/_my_model_pkg.py
```

Pre-commit basics exercised by the configured hooks:

- trailing whitespace removal
- end-of-file fixer
- YAML and AST checks
- ruff lint with `--fix`
- ruff formatting
- notebook QA hooks for notebook files

Do not run notebook QA or docs builds for ordinary Python-only component work unless the task explicitly modifies notebooks or documentation examples.

## 6) When to broaden tests

Broaden beyond focused selections only after the component passes import, registry, and tiny CPU integration checks.

Broaden when:

- a new tag changes registry filtering behavior
- a new metric changes shared metric base behavior
- a new data module changes collate behavior
- a model claims multi-target, quantile, or distribution support
- optional dependency guards were added

Do not broaden just to debug a basic `_pkg()` naming mismatch or a tensor-shape error; those are faster to fix with focused tests and a manual tiny fixture.
