# Modin experimental XGBoost

`modin.experimental.xgboost` provides Ray-backed distributed wrappers around XGBoost training.

## Requirements

- `MODIN_ENGINE=Ray` before importing `modin.pandas`.
- `ray`, `xgboost`, and `scikit-learn` for the bundled smoke.
- A compatible XGBoost package that exposes the legacy APIs used by this Modin implementation: `xgboost.RabitTracker` and `xgboost.rabit`.

The inspected dependency set had an importable XGBoost package but lacked `xgboost.rabit`; treat training as optional-unavailable until a compatible XGBoost version is installed.

## DMatrix contract

`DMatrix(data, label=None, missing=None, silent=False, feature_names=None, feature_types=None, feature_weights=None, enable_categorical=None)` expects:

- `data` is a `modin.pandas.DataFrame`.
- `label`, when provided, is a `modin.pandas.DataFrame` or `modin.pandas.Series`.
- Object dtype feature columns are rejected.
- `feature_names` must be unique, match the number of columns, be strings, and avoid `[`, `]`, and `<`.
- `feature_types` may be a string or list of strings.
- The constructor stores row count, column count, feature metadata, missing-value handling, and partition references.

The Modin wrapper does not support every native XGBoost `DMatrix` argument. Source notes explicitly call out unsupported `weight`, `base_margin`, `nthread`, `group`, `qid`, `label_lower_bound`, and `label_upper_bound` parameters.

## Training contract

```python
import os
os.environ["MODIN_ENGINE"] = "Ray"


def main():
    import modin.pandas as pd
    import modin.experimental.xgboost as mxgb

    X = pd.DataFrame({"f0": [0.0, 1.0, 2.0, 3.0], "f1": [1.0, 1.0, 0.0, 0.0]})
    y = pd.Series([0, 0, 1, 1])
    dtrain = mxgb.DMatrix(X, label=y, feature_names=["f0", "f1"], feature_types=["q", "q"])
    result = {}
    booster = mxgb.train(
        {"objective": "binary:logistic", "eval_metric": "logloss"},
        dtrain,
        num_boost_round=1,
        evals=[(dtrain, "train")],
        evals_result=result,
        num_actors=1,
        verbose_eval=False,
    )
    print(booster.predict(dtrain).shape, result)


if __name__ == "__main__":
    main()
```

`train(params, dtrain, *args, evals=(), num_actors=None, evals_result=None, **kwargs)` delegates to a Ray implementation and raises if the current engine is not Ray. Keep `num_actors` small for local smokes.

## Prediction caveats

Prediction validates feature names. If the training data had explicit feature names, prediction data must carry compatible names. Mismatched or missing feature metadata can raise `ValueError` when materialized.
