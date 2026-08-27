# Tabular workflows

This file gives the practical tabular routes that users most often need.

## 1. End-to-end search

Use `search(...)` when you want Auto-PyTorch to optimize a tabular model family and build an ensemble for you.

```python
from autoPyTorch.api.tabular_classification import TabularClassificationTask

api = TabularClassificationTask(seed=42)
api.search(
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
    optimize_metric="accuracy",
    total_walltime_limit=300,
    func_eval_time_limit_secs=50,
)

y_pred = api.predict(X_test)
score = api.score(y_pred, y_test)
print(api.show_models())
```

For regression, use `TabularRegressionTask` and set `optimize_metric="r2"` or another regression metric.

## 2. Fit a single configuration

Use `get_dataset(...)`, `get_search_space(...)`, and `fit_pipeline(...)` when you already know the configuration you want to test.

```python
from autoPyTorch.api.tabular_classification import TabularClassificationTask
from autoPyTorch.datasets.resampling_strategy import HoldoutValTypes

estimator = TabularClassificationTask(resampling_strategy=HoldoutValTypes.holdout_validation)
dataset = estimator.get_dataset(X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test)
config = estimator.get_search_space(dataset).get_default_configuration()
pipeline, run_info, run_value, dataset = estimator.fit_pipeline(
    dataset=dataset,
    configuration=config,
    budget_type="epochs",
    budget=5,
    run_time_limit_secs=75,
)
```

Use this route when you want to debug one pipeline, compare two configurations, or reason about the resulting `RunInfo` and `RunValue`.

## 3. Refit the final model

After a successful search, call `refit(...)` when you want to retrain the selected ensemble on the full training set.

```python
api.refit(
    X_train=X_train,
    y_train=y_train,
    X_test=X_test,
    y_test=y_test,
    dataset_name="my-dataset",
)
```

## 4. Control the search space

Use the component filters and updates when you need to narrow or reshape the search.

- `include_components` to keep only named components
- `exclude_components` to drop named components
- `search_space_updates` to change specific hyperparameter ranges or defaults
- `portfolio_selection='greedy'` to warm-start from the built-in greedy portfolio

Example pattern:

```python
from autoPyTorch.utils.hyperparameter_search_space_update import HyperparameterSearchSpaceUpdates

updates = HyperparameterSearchSpaceUpdates()
updates.append(node_name="data_loader", hyperparameter="batch_size", value_range=[16, 512], default_value=32)
updates.append(node_name="network_backbone", hyperparameter="ResNetBackbone:dropout", value_range=[0, 0.5], default_value=0.2)

api = TabularClassificationTask(
    search_space_updates=updates,
    include_components={"network_backbone": ["MLPBackbone", "ResNetBackbone"]},
)
```

## 5. Use traditional learners intentionally

The tabular search can include a traditional-learners path. This is useful when:

- the dataset is small
- you want a strong non-neural baseline
- you need a faster debug route before a full neural search

The available traditional learners are:

- LightGBM
- CatBoost
- Random Forest
- Extra Trees
- SVM
- KNN

## 6. Validate and compress inputs

The tabular validators normalize categorical data, encode labels, and can reduce large datasets.

Common patterns:

- use pandas DataFrames when you want dtype-aware categorical detection
- pass `feat_types` when NumPy data hides categorical columns
- use dataset compression only when the data is too large for the memory budget

## 7. Inspect the result

After a run, use:

- `show_models()` to see the final ensemble members and weights
- `sprint_statistics()` to read a text summary of the search
- `plot_perf_over_time(...)` to visualize how the incumbent evolved

For plotting, use `PlotSettingParams` when you want to save a file or customize axes labels.

## 8. When to stop and read troubleshooting

Read `references/troubleshooting.md` if you hit:

- `ModuleNotFoundError` for the `automl_common` submodule
- version conflicts around `scikit-learn`, `torch`, or compiled wheels
- OpenML download failures in the example scripts
- validator errors about inconsistent shapes or unsupported data types
