# Taskflows, Callbacks, Metrics, and Scalers

## Purpose

Read this reference when you need to customize how data flows through the runner, how a callback hooks into training, or how metrics and scalers are applied.

## Runner hook order

From source inspection of `BasicTSRunner` and `BasicTSCallback`:

1. `on_train_start`
2. `on_epoch_start`
3. `on_step_start`
4. `taskflow.preprocess`
5. model forward
6. `on_compute_loss`
7. loss computation
8. `on_backward`
9. `on_optimizer_step`
10. optimizer step
11. `taskflow.postprocess`
12. metric updates
13. `on_step_end`
14. `on_epoch_end`

Validation and testing use the same taskflow pattern but skip the backward and optimizer stages.

## Taskflow contract

Every taskflow implements:

```python
preprocess(runner, data)
postprocess(runner, forward_return)
get_weight(forward_return)
```

### Forecasting taskflow

- builds `inputs_mask` and `targets_mask` from `null_val`
- applies the configured scaler when present
- fills missing values with `null_to_num`
- rescales predictions during postprocess when `rescale=True`
- uses the number of valid target elements as the weight

### Classification taskflow

- masks invalid values on `inputs`
- applies the configured scaler when present
- converts model logits into class ids with `argmax` during postprocess
- uses batch size as the metric weight

### Imputation taskflow

- masks null values on `inputs`
- applies the configured scaler when present
- creates a self-supervised reconstruction target at runtime
- applies a random reconstruction mask
- uses the number of masked target elements as the weight

## Callback catalog

| Callback | Purpose | Notable hook |
| --- | --- | --- |
| `AddAuxiliaryLoss` | Adds named auxiliary loss values to the main loss | `on_compute_loss` |
| `GradientClipping` | Clips gradient norm after backward | `on_optimizer_step` |
| `EarlyStopping` | Stops training when validation no longer improves | `on_validate_end` |
| `GradAccumulation` | Skips optimizer steps until enough backward passes have happened | `on_backward` |
| `NoBP` | Disables backpropagation entirely | `on_train_start` |
| `SelectiveLearning` | Advanced selective-learning callback that relies on an estimator checkpoint | `on_train_start` / `on_compute_loss` / `on_epoch_end` |

## Metric behavior

The runner stores metrics in `ALL_METRICS` and maps the metric name to the callable.

### Built-in metrics

- `MAE`
- `MSE`
- `RMSE`
- `MAPE`
- `WAPE`
- `SMAPE`
- `R2`
- `CORR`
- `HUBER`
- `Accuracy`

### Metric call rules

- the runner passes the keys that the metric signature accepts
- if a metric expects `prediction` or `targets`, BasicTS provides them when available
- metrics can also consume `targets_mask` or other keys returned by the model/taskflow

### Special meter note

`RMSE` uses a dedicated meter because it is not correct to average the squared value and then take a plain arithmetic mean.

## Scaler behavior

`ZScoreScaler` and `MinMaxScaler` both implement:

- `fit(data)`
- `transform(input_data, mask=None)`
- `inverse_transform(input_data, mask=None)`

### What the scaler sees

The runner fits the scaler on `dataset.data` from the training split.

This means:

- the dataset class must expose a `data` property
- the property should return the array view the scaler should learn from
- if the property is missing or malformed, scaler fitting fails during training setup

## Practical examples

### Custom metric

```python
def my_metric(prediction, targets, targets_mask=None):
    ...
```

### Custom callback

```python
from basicts.runners.callback import BasicTSCallback

class MyCallback(BasicTSCallback):
    def on_epoch_end(self, runner, *args, **kwargs):
        ...
```

### Auxiliary losses

If a model returns:

```python
{
    "prediction": prediction,
    "freq_loss": freq_loss,
}
```

Attach:

```python
AddAuxiliaryLoss(["freq_loss"])
```

## Evidence sources

- `docs/runner_and_pipeline.md`
- `docs/metrics_design.md`
- `docs/scaler_design.md`
- `src/basicts/runners/basicts_runner.py`
- `src/basicts/runners/taskflow/*.py`
- `src/basicts/runners/callback/*.py`
- `src/basicts/metrics/*.py`
- `src/basicts/scaler/*.py`
- `src/basicts/utils/mask.py`
- installed-package inspection in the CPU environment
