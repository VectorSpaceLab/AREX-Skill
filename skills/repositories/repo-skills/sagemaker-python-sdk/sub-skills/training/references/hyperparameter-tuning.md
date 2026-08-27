# Hyperparameter tuning

Use this reference when the task is to search over training parameters with
`HyperparameterTuner` or to inspect tuning results afterward.

## Import map

```python
from sagemaker.train import ModelTrainer
from sagemaker.train.tuner import HyperparameterTuner
from sagemaker.core.training.configs import SourceCode, Compute, InputData
from sagemaker.parameter import ContinuousParameter, IntegerParameter, CategoricalParameter
```

## Tuner constructor

`HyperparameterTuner` is built around a base `ModelTrainer` plus:

- `objective_metric_name`
- `hyperparameter_ranges`
- `metric_definitions`
- `strategy`
- `objective_type`
- `max_jobs`
- `max_parallel_jobs`
- `max_runtime_in_seconds`
- `warm_start_config`
- `strategy_config`
- `completion_criteria_config`
- `early_stopping_type`
- `random_seed`
- `autotune`
- `hyperparameters_to_keep_static`

## Metrics and search spaces

- Use `metric_definitions` when the metric must be extracted from logs by regex.
- Use `ContinuousParameter`, `IntegerParameter`, and `CategoricalParameter` for
  the search space.
- Use `objective_type="Maximize"` or `"Minimize"` according to the metric.
- Keep the metric regex aligned with the training container logs.

## Main flow

1. Build a `ModelTrainer` with the same source code and data layout you would
   use for a normal training job.
2. Construct the tuner with an objective metric and parameter ranges.
3. Call `tune(inputs=..., wait=True)` to start the tuning job.
4. Use `analytics()` after the tuning job exists to inspect the results.
5. Use `best_training_job()` or `latest_tuning_job` when you need the winning
   job.

## Warm start and autotune

- Use warm start configuration when the search should build on existing tuning
  runs.
- Use `autotune=True` when the SDK should infer some tuning settings.
- If `hyperparameters_to_keep_static` is set, autotune must also be enabled.

## Safe pattern

```python
trainer = ModelTrainer(
    training_image="<training-image-uri>",
    role="<role-name-or-arn>",
    source_code=SourceCode(source_dir="./src", entry_script="train.py"),
    compute=Compute(instance_type="ml.m5.xlarge", instance_count=1),
)

tuner = HyperparameterTuner(
    model_trainer=trainer,
    objective_metric_name="validation:accuracy",
    hyperparameter_ranges={
        "lr": ContinuousParameter(1e-5, 1e-2),
        "batch_size": IntegerParameter(16, 128),
    },
    max_jobs=10,
    max_parallel_jobs=2,
)
```

## Troubleshooting cues

- missing or mismatched metric regex
- ranges omitted without `autotune=True`
- invalid `hyperparameters_to_keep_static` configuration
- trying to analyze results before a tuning job exists
