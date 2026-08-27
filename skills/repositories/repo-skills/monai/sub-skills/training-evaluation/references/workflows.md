# Training and Evaluation Workflows

## Choose plain PyTorch or MONAI engines

| Situation | Recommended pattern | Why |
|---|---|---|
| Small custom experiment, unusual control flow, or no Ignite dependency available | Plain PyTorch loop with MONAI data/model/loss/metric components | Keeps control explicit and avoids optional Ignite requirements. |
| Standard supervised training with image/label batches | `monai.engines.SupervisedTrainer` | Provides iteration output keys, AMP handling, gradient accumulation, postprocessing, metrics, and handler attachment. |
| Validation/evaluation pass with MONAI metrics and postprocessing | `monai.engines.SupervisedEvaluator` | Runs in eval mode by default, stores metrics in `engine.state.metrics`, and can be triggered by `ValidationHandler`. |
| Config-driven bundle run or verify | MONAI Bundle CLI/config parser | Do not duplicate bundle workflows manually; route to the bundle sub-skill. |

MONAI engines are Ignite engines with MONAI conventions. They do not replace PyTorch modules, losses, optimizers, dataloaders, or transforms; they coordinate those components and expose Ignite events for handlers.

## Minimal supervised engine shape

1. Build data loaders that yield either `(image, label)` pairs or dictionaries containing MONAI common keys such as `"image"` and `"label"`.
2. Move the network to the chosen device before creating the trainer/evaluator.
3. Create a PyTorch optimizer and loss function; use MONAI losses/metrics when appropriate, but keep primitive selection in the modeling sub-skill.
4. Create a `SupervisedEvaluator` for validation before the trainer if the trainer should call validation.
5. Attach validation, stats, checkpoint, LR, and tracking handlers through `val_handlers` and `train_handlers`.
6. Call `trainer.run()`; inspect `trainer.state`, `trainer.state.metrics`, `evaluator.state.metrics`, and checkpoint files for results.

A typical handler list is:

```python
val_handlers = [
    StatsHandler(output_transform=lambda output: None),
    CheckpointSaver(save_dir="runs", save_dict={"network": network}, save_key_metric=True, key_metric_name="val_mean_dice"),
]
train_handlers = [
    ValidationHandler(interval=1, validator=evaluator),
    StatsHandler(output_transform=lambda output: output["loss"]),
    CheckpointSaver(save_dir="runs", save_dict={"network": network, "optimizer": optimizer}, save_final=True),
]
```

Put exception-saving checkpoint handlers before `StatsHandler` when both listen for exceptions; Ignite may trigger only the first `EXCEPTION_RAISED` handler.

## Trainer and evaluator wiring

### Trainer

Use `SupervisedTrainer` when each iteration should perform `prepare_batch`, network forward, loss, backward, optimizer step, postprocessing, and metric updates.

Important decisions:

- `prepare_batch`: defaults to accepting tensor, tensor pair, or dict with `image`/`label`; provide `PrepareBatchExtraInput` or a custom callable for extra model inputs.
- `inferer`: defaults to `SimpleInferer`; pass another inferer when the training forward needs a MONAI inferer abstraction.
- `postprocessing`: runs after model computation; set `decollate=True` when postprocessing expects lists of channel-first samples.
- `key_train_metric` and `additional_metrics`: Ignite metrics attached to the trainer; they update `engine.state.metrics` at epoch completion.
- `train_handlers`: sequence of objects with `attach(engine)` such as `StatsHandler`, `ValidationHandler`, `CheckpointSaver`, and LR/tracking handlers.
- `amp`: enables MONAI's autocast/scaler path; prefer `False` for CPU smoke tests and only enable after confirming CUDA and numerical behavior.
- `accumulation_steps`: accumulates gradients across mini-batches; MONAI flushes at epoch end when needed.

### Evaluator

Use `SupervisedEvaluator` for validation/evaluation. It performs `prepare_batch`, forward, optional inferer, postprocessing, and metric updates without optimizer steps.

Important decisions:

- `mode="eval"` is default and calls `model.eval()` during evaluation; `mode="train"` exists for special validation procedures.
- `key_val_metric` names the metric used by `CheckpointSaver(save_key_metric=True)` when `key_metric_name` is omitted or coordinated through engine state.
- `val_handlers` commonly include `StatsHandler`, `CheckpointSaver` for best metric, `MetricsSaver`, or tracking handlers.
- `run(global_epoch)` is called by `ValidationHandler`; it synchronizes validation epoch reporting with the trainer epoch.

## Validation and checkpoint flow

Use `ValidationHandler(interval=N, validator=evaluator, epoch_level=True)` to run validation every `N` epochs. Set `epoch_level=False` for iteration intervals. Set `exec_at_start=True` to validate the initial model before training.

Checkpoint patterns:

- Final checkpoint: `CheckpointSaver(save_final=True, save_dict={"network": net, "optimizer": opt})` saves at completion and exception.
- Best metric checkpoint: `CheckpointSaver(save_key_metric=True, key_metric_name="val_mean_dice", key_metric_n_saved=1)` saves when `engine.state.metrics[key_metric_name]` improves.
- Fixed filename: set `final_filename` or `key_metric_filename`; for a fixed key metric filename, keep `key_metric_n_saved=1`.
- Smaller-is-better metrics: use `key_metric_negative_sign=True` for losses or distances.
- Periodic checkpoints: set `save_interval`, `epoch_level`, and `n_saved`.
- Resume key-metric tracking only when the original saver used `key_metric_save_state=True` and the new saver loads that state.

Use a relative or user-provided run directory, create it before training when needed, and never hard-code machine-specific paths.

## Stats, metrics, and output transforms

MONAI engine iteration outputs typically use dictionary keys from `monai.utils.enums.CommonKeys`: `"image"`, `"label"`, `"pred"`, and `"loss"`. Handlers and metrics must extract the right values from `engine.state.output`.

Examples:

- Training loss logging: `StatsHandler(output_transform=lambda output: output["loss"])`.
- Validation metric logging: `StatsHandler(output_transform=lambda output: None)` and rely on epoch metrics.
- Dice metric handler: `MeanDice(output_transform=from_engine(["pred", "label"]))` when output contains those keys.

Metrics update at iteration events and aggregate/reset at epoch events through Ignite. If validation metrics are stale, check that validation actually ran, the metric handler is attached to the evaluator rather than the trainer, `output_transform` extracts current predictions and labels, and epoch completion fired.

## Optimizers and schedulers

MONAI provides optimizer helpers in addition to PyTorch optimizers:

- `generate_param_groups(network, layer_matches, match_types, lr_values, include_others=True)` builds parameter groups for layer-specific learning rates.
- `WarmupCosineSchedule(optimizer, warmup_steps, t_total, end_lr=0.0, cycles=0.5, warmup_multiplier=0)` provides linear warmup followed by cosine decay.
- `Novograd` is available for training workflows that intentionally choose it.
- `LrScheduleHandler` and parameter scheduler handlers can step schedules from Ignite events; confirm whether the schedule should step per iteration or per epoch.

## AMP, TF32, compile, and distributed notes

- `amp=True` is useful for CUDA training/evaluation but is not a correctness requirement; keep CPU examples with `amp=False`.
- Use `amp_kwargs` for autocast arguments only after confirming the target device and PyTorch AMP API behavior.
- TF32 can affect numerical reproducibility on NVIDIA Ampere-or-newer GPUs; explicitly inspect or set PyTorch TF32 flags when convergence or reproducibility matters.
- `compile=True` uses `torch.compile`; MONAI converts `MetaTensor` inputs around the compiled forward path. Treat it as optional and benchmark before recommending it.
- For distributed training, use appropriate distributed samplers/loaders, rank-aware logging/checkpointing, and worker seeding. Do not assume every handler is safe to execute on every rank without checking its distributed behavior.
- Optional experiment tracking handlers such as TensorBoard, MLflow, and ClearML require their own packages and configured services; include graceful fallbacks when those extras are not installed.
