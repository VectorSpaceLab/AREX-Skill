# Tuning Workflows

## Ordinary tuning with the base estimators

The ordinary estimators support tuning through `eval_metric` and `tuning_config`.

### Classifier tuning metrics

Supported classifier metrics include:

- `f1`
- `accuracy`
- `balanced_accuracy`
- `roc_auc`
- `log_loss`

### Tuning configuration

`TuningConfig` and `ClassifierTuningConfig` control:

- whether temperature calibration is enabled,
- the holdout fraction used during tuning,
- the number of tuning folds,
- and, for classification, whether decision thresholds should also be tuned.

## Useful helper functions

- `resolve_tuning_config` — resolves `auto` tuning values.
- `find_optimal_temperature` — calibrates softmax temperature.
- `find_optimal_classification_thresholds` — tunes per-class decision thresholds.
- `get_tuning_splits` — generates stratified tuning splits.

## When tuning is a good fit

- The model already works, but its probabilities need calibration.
- The user cares about a metric like log-loss or F1 rather than default labels.
- The user has enough data for a holdout-based calibration step.

## When tuning is not enough

- The user wants to change the model weights.
- The user needs gradients through the inputs.
- The user wants persistent checkpoints or a full training loop.

In those cases, move to the fine-tuning or differentiable-input references.
