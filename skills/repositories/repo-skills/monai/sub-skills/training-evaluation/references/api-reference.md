# Training and Evaluation API Reference

This reference summarizes the MONAI APIs most often needed when assembling training/evaluation loops. It intentionally omits model, loss, metric-design, data-pipeline, Bundle, and Auto3DSeg details owned by other sub-skills.

## Engines

| API | Concise signature | Notes |
|---|---|---|
| `SupervisedTrainer` | `(device, max_epochs, train_data_loader, network, optimizer, loss_function, epoch_length=None, non_blocking=False, prepare_batch=default_prepare_batch, iteration_update=None, inferer=None, postprocessing=None, key_train_metric=None, additional_metrics=None, metric_cmp_fn=default_metric_cmp_fn, train_handlers=None, amp=False, event_names=None, event_to_attr=None, decollate=True, optim_set_to_none=False, to_kwargs=None, amp_kwargs=None, compile=False, compile_kwargs=None, accumulation_steps=1)` | Standard supervised training engine. Default iteration returns output with image, label, pred, and loss-style values. `accumulation_steps` must be positive. |
| `SupervisedEvaluator` | `(device, val_data_loader, network, epoch_length=None, non_blocking=False, prepare_batch=default_prepare_batch, iteration_update=None, inferer=None, postprocessing=None, key_val_metric=None, additional_metrics=None, metric_cmp_fn=default_metric_cmp_fn, val_handlers=None, amp=False, mode="eval", event_names=None, event_to_attr=None, decollate=True, to_kwargs=None, amp_kwargs=None, compile=False, compile_kwargs=None)` | Standard supervised evaluator. Runs for one validation pass and defaults to eval mode. `run(global_epoch=1)` syncs reporting with the trainer epoch. |
| `Evaluator` | `(device, val_data_loader, epoch_length=None, non_blocking=False, prepare_batch=default_prepare_batch, iteration_update=None, postprocessing=None, key_val_metric=None, additional_metrics=None, metric_cmp_fn=default_metric_cmp_fn, val_handlers=None, amp=False, mode="eval", event_names=None, event_to_attr=None, decollate=True, to_kwargs=None, amp_kwargs=None)` | Base evaluator for custom `_iteration` implementations. |
| `Trainer` | Inherits MONAI `Workflow`; concrete subclasses define iteration behavior. | `run()` initializes AMP scaler when enabled and then delegates to the Ignite workflow. |

## Batch preparation

| API | Concise signature | Notes |
|---|---|---|
| `default_prepare_batch` | `(batchdata, device=None, non_blocking=False, **kwargs)` | Accepts a single tensor, a two-item tensor sequence, or a dict. Dicts with `"image"` and tensor `"label"` return `(image, label)` on device; image-only dicts return `(image, None)`. |
| `PrepareBatchDefault` | `().__call__(batchdata, device=None, non_blocking=False, **kwargs)` | Callable wrapper around `default_prepare_batch`. |
| `PrepareBatchExtraInput` | `(extra_keys).__call__(batchdata, device=None, non_blocking=False, **kwargs)` | Returns `(image, label, args, kwargs)` for networks or inferers needing extra inputs. `extra_keys` may be a key, list/tuple of keys, or mapping from model kwarg names to batch keys. |

Custom `prepare_batch` callables should accept `batchdata`, `device`, `non_blocking`, and `**kwargs`; move only tensor values that must be on the compute device.

## Iteration events and engine state

MONAI registers custom iteration events for trainer workflows:

| Event | Meaning |
|---|---|
| `IterationEvents.FORWARD_COMPLETED` | Network/inferer forward completed. |
| `IterationEvents.LOSS_COMPLETED` | Loss computation completed. |
| `IterationEvents.BACKWARD_COMPLETED` | Backward pass completed. |
| `IterationEvents.MODEL_COMPLETED` | Model-related iteration work completed. |
| `IterationEvents.INNER_ITERATION_STARTED` / `INNER_ITERATION_COMPLETED` | Inner loop boundaries for workflows that have nested iteration logic. |

Common state locations:

- `engine.state.batch`: current batch before/inside iteration.
- `engine.state.output`: current iteration output; MONAI supervised engines usually use dict keys such as `"image"`, `"label"`, `"pred"`, and `"loss"`.
- `engine.state.metrics`: aggregated metrics at epoch completion.
- `engine.state.metric_details`: per-item or per-class details for handlers such as `MeanDice` when enabled.
- `engine.state.best_metric` and `engine.state.best_metric_epoch`: maintained by MONAI workflow key metric logic.

## Core handlers

| API | Concise signature | Attach to | Notes |
|---|---|---|---|
| `StatsHandler` | `(iteration_log=True, epoch_log=True, epoch_print_logger=None, iteration_print_logger=None, output_transform=lambda x: x[0], global_epoch_transform=lambda x: x, state_attributes=None, name="monai.handlers.StatsHandler", tag_name="Loss", key_var_format="{}: {:.4f} ")` | Trainer or evaluator | Logs iteration output and epoch metrics. Set `output_transform` for MONAI dict outputs; ensure logger level is `INFO` or lower. |
| `ValidationHandler` | `(interval, validator=None, epoch_level=True, exec_at_start=False)` | Trainer | Runs a MONAI `Evaluator` every N epochs or iterations. Use `set_validator()` before training if constructed without a validator. |
| `CheckpointSaver` | `(save_dir, save_dict, name=None, file_prefix="", save_final=False, final_filename=None, save_key_metric=False, key_metric_name=None, key_metric_n_saved=1, key_metric_filename=None, key_metric_save_state=False, key_metric_greater_or_equal=False, key_metric_negative_sign=False, epoch_level=True, save_interval=0, n_saved=None)` | Trainer or evaluator | Saves final, best-metric, or periodic checkpoint files. Requires non-empty `save_dict`. Metric checkpoints require scalar metrics. |
| `MeanDice` | `(include_background=True, reduction="mean", num_classes=None, output_transform=lambda x: x, save_details=True, return_with_label=False)` | Evaluator or trainer with segmentation outputs | Wraps MONAI `DiceMetric` as an Ignite metric handler. Use `from_engine(["pred", "label"])` when output is a dict. |
| `LrScheduleHandler` | Scheduler handler API in `monai.handlers` | Trainer | Steps learning-rate schedules from Ignite events; choose iteration versus epoch stepping deliberately. |
| `ParamSchedulerHandler` | Parameter scheduler handler API in `monai.handlers` | Trainer or evaluator | Drives Ignite-compatible parameter schedulers. |
| `MetricsSaver` | Metrics persistence handler API in `monai.handlers` | Evaluator | Writes metrics after evaluation; choose output directories and formats explicitly. |
| Tracking handlers | TensorBoard, MLflow, ClearML handlers in `monai.handlers` | Trainer or evaluator | Optional extras. Guard imports and provide fallback logging when packages/services are unavailable. |

Handler lists are attached in order by MONAI workflows. Order matters when handlers listen to the same Ignite event, especially `EXCEPTION_RAISED`.

## Optimizer utilities

| API | Concise signature | Notes |
|---|---|---|
| `generate_param_groups` | `(network, layer_matches, match_types, lr_values, include_others=True)` | Builds parameter groups for a PyTorch optimizer. `match_types` are `"select"` for module selectors or `"filter"` for `named_parameters()` filters. |
| `WarmupCosineSchedule` | `(optimizer, warmup_steps, t_total, end_lr=0.0, cycles=0.5, last_epoch=-1, warmup_multiplier=0)` | Linear warmup then cosine decay. `warmup_multiplier` must be between 0 and 1. |
| `LinearLR` | `(optimizer, end_lr, num_iter, last_epoch=-1)` | Linearly increases LR over a fixed number of iterations. |
| `ExponentialLR` | `(optimizer, end_lr, num_iter, last_epoch=-1)` | Exponentially increases LR over a fixed number of iterations. |
| `Novograd` | PyTorch optimizer class in `monai.optimizers` | Use only when the training recipe intentionally calls for Novograd; otherwise ordinary PyTorch optimizers are valid. |

## Import checklist

Use these imports in examples only when the target environment has Ignite installed:

```python
from monai.engines import SupervisedTrainer, SupervisedEvaluator, PrepareBatchExtraInput
from monai.handlers import CheckpointSaver, MeanDice, StatsHandler, ValidationHandler, from_engine
from monai.optimizers import WarmupCosineSchedule, generate_param_groups
```

If importing `monai.engines` or `monai.handlers` fails with an Ignite-related message, install MONAI with the Ignite extra or install a compatible `pytorch-ignite` package for the MONAI version in use.
