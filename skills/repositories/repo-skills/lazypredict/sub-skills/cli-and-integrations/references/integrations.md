# Integrations and Optional Backends

## MLflow tracking

Lazy Predict's MLflow helper checks whether the `mlflow` package is installed
and `MLFLOW_TRACKING_URI` is set. When both are true, it sets the tracking URI
and enables MLflow autologging.

```python
import os
os.environ['MLFLOW_TRACKING_URI'] = 'sqlite:///mlflow.db'

from lazypredict.Supervised import LazyRegressor
reg = LazyRegressor(verbose=0, ignore_warnings=True)
scores, _ = reg.fit(X_train, X_test, y_train, y_test)
```

The package does not start an MLflow UI or tracking server. For Databricks or a
remote server, verify credentials and tracking URI outside Lazy Predict first.

## Dask and PySpark auto-conversion

`lazypredict.distributed.auto_convert_dataframe(data, name='data')` passes
through pandas and NumPy inputs. When Dask or PySpark objects are supplied and
the corresponding optional packages are installed, Lazy Predict can collect or
convert them for local sklearn-style fitting.

Do not use this path blindly for large distributed data: conversion may collect
data to the driver. For large Spark-native training, use the Spark classes
instead.

## Spark MLlib classes

The optional Spark surface exposes `LazySparkClassifier` and
`LazySparkRegressor` in `lazypredict.spark`. Instantiating or using them requires
`pyspark` and a working Spark/JVM runtime.

```python
from lazypredict.spark import LazySparkClassifier, LazySparkRegressor
```

If `pyspark` is not installed, Spark class construction is expected to raise an
ImportError rather than silently falling back to local pandas/sklearn behavior.

## GPU acceleration

`use_gpu=True` is available on supervised and forecasting APIs. Supported
backend families include:

- XGBoost with CUDA parameters;
- LightGBM with GPU parameters;
- CatBoost with GPU task type;
- cuML RAPIDS models when installed;
- PyTorch CUDA for LSTM/GRU and TimesFM forecasting.

Lazy Predict's GPU parameter helper uses PyTorch CUDA availability. A visible
GPU is not enough; the active Python environment must have compatible optional
packages. When GPU is not available, many paths warn and fall back to CPU.

## Intel Extension for Scikit-learn

If `scikit-learn-intelex` is installed, Lazy Predict attempts to patch sklearn
for Intel CPU acceleration at import time. Absence of this package is normal and
should not block base workflows.

## Optional dependency matrix

Run the root checker to see optional module availability without installing or
starting anything:

```bash
python ../../../scripts/check_lazypredict_env.py --json
```

Important optional modules include `xgboost`, `lightgbm`, `catboost`,
`statsmodels`, `pmdarima`, `torch`, `timesfm`, `optuna`, `shap`, `interpret`,
`flaml`, `pyspark`, `dask`, `mlflow`, `matplotlib`, `category_encoders`,
`sklearnex`, and `cuml`.
