# Training and Evaluation Troubleshooting

## Quick diagnosis matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| Importing `monai.engines` or a handler raises an Ignite-related error | Ignite is an optional dependency for MONAI engine/handler workflows | Install MONAI with the Ignite extra if available for the target package version, or install a compatible `pytorch-ignite`; otherwise use a plain PyTorch loop with MONAI components. |
| `default_prepare_batch` raises an assertion or key error | Loader batch is not a single tensor, two-item tensor sequence, or dict with expected keys | Normalize the data pipeline to yield `(image, label)` or dict keys `"image"`/`"label"`; for extra model inputs use `PrepareBatchExtraInput` or a custom callable. |
| Model receives missing or unexpected extra arguments | `prepare_batch` return shape does not match network/inferer call path | For positional extras, pass `PrepareBatchExtraInput(["key1", "key2"])`; for keyword extras, pass `PrepareBatchExtraInput({"model_arg": "batch_key"})`; keep non-tensor metadata on CPU unless the model needs it. |
| `StatsHandler` logs nothing | Logger level is above `INFO`, iteration logging disabled, or `output_transform` fails silently in custom logging | Configure the Ignite/MONAI logger at `INFO`; set `StatsHandler(output_transform=lambda output: output["loss"])` for supervised trainer dict outputs; use epoch metrics for evaluator logging. |
| Training crashes during exception handling but final checkpoint is missing | Another handler consumed `EXCEPTION_RAISED` first | Put `CheckpointSaver(save_final=True, ...)` before `StatsHandler` and other exception handlers in the handler list. |
| Best metric checkpoint never appears | Metric name mismatch, metric is non-scalar, evaluator handler attached to trainer, or validation never ran | Confirm `ValidationHandler` is attached to the trainer, metric handler is attached to the evaluator, `engine.state.metrics[key_metric_name]` exists and is scalar, and `save_key_metric=True` uses the same metric name. |
| Checkpoints are written with surprising names | `file_prefix`, `final_filename`, `key_metric_filename`, `epoch_level`, or `save_interval` settings differ from expectations | Use `final_filename` for a fixed final name; use `key_metric_filename` only with `key_metric_n_saved=1`; check whether periodic saves are epoch- or iteration-level. |
| Old best-metric comparison is lost after resume | `CheckpointSaver` internal state was not saved or loaded | Set `key_metric_save_state=True` in the original saver and load its state into the new saver when resuming. |
| Validation metrics appear stale | Metric reset/aggregation event did not run, validation is not triggered, or output transform reads previous state | Attach metric handlers to the evaluator; ensure evaluator reaches `EPOCH_COMPLETED`; use `from_engine(["pred", "label"])` or an explicit output transform; check `ValidationHandler(interval=..., exec_at_start=...)`. |
| Mean Dice reports shape mismatch | Predictions/labels are not both batch-first tensors or lists of channel-first tensors in the expected class format | Decollate and postprocess predictions/labels consistently; set `num_classes` when using class-index tensors; verify `include_background` and one-hot conversion choices. |
| AMP fails on CPU or non-CUDA device | `amp=True` or CUDA autocast assumptions were copied into a CPU workflow | Keep `amp=False` for CPU examples; only enable AMP after checking CUDA availability and using device-appropriate `amp_kwargs`. |
| Training results differ across machines | TF32, AMP, random seeds, DataLoader workers, or distributed samplers differ | Set deterministic controls where needed, inspect PyTorch TF32 flags, seed workers/samplers, and document any intentional precision/performance trade-off. |
| Distributed run duplicates logs/checkpoints | Handlers execute on every rank or samplers are not distributed-aware | Use rank-aware logging and checkpoint conditions; configure distributed samplers and call sampler epoch setters as appropriate; avoid writing the same checkpoint from every process. |
| Data loading hangs or workers duplicate samples | Worker count, persistent workers, thread loaders, cache strategy, or distributed sampling is mismatched | Start with `num_workers=0` for debugging; verify sampler length and epoch behavior; coordinate cache/thread loaders with the data sub-skill. |
| TensorBoard, MLflow, or ClearML handler import fails | Tracking backend is optional and not installed/configured | Guard tracking imports, fall back to `StatsHandler` or plain logging, and document the extra package/service requirement. |
| `WarmupCosineSchedule` raises `ValueError` | `warmup_multiplier` is outside `[0, 1]` | Use a multiplier between 0 and 1; confirm `t_total` covers the intended number of scheduler steps. |
| Scheduler changes LR at wrong cadence | Scheduler handler is attached to an epoch event when per-iteration stepping was intended, or vice versa | Decide whether the schedule is iteration-based or epoch-based; set handler/event wiring consistently with `t_total` and optimizer steps. |

## Debugging handler order

When behavior depends on event order, list the intended events before coding:

1. Trainer starts.
2. Optional `ValidationHandler(exec_at_start=True)` runs evaluator.
3. Each training iteration prepares batch, forwards, computes loss, backpropagates, steps optimizer, and fires iteration events.
4. Epoch completion aggregates metrics, logs stats, runs validation if interval matches, and may save periodic checkpoints.
5. Evaluator epoch completion aggregates validation metrics and may save best-metric checkpoints.
6. Trainer completion or exception triggers final checkpoint handlers.

Attach handlers to the engine that owns the event. A validation metric handler belongs on the evaluator; the validation trigger belongs on the trainer.

## Debugging `prepare_batch`

Use this checklist for batch mismatches:

- Print or inspect one batch from the loader before creating the engine.
- Confirm the batch keys are `"image"` and `"label"` for the default path.
- Confirm values that need device transfer are tensors; keep strings, paths, and metadata out of tensor-only logic.
- For models with extra inputs, map batch keys explicitly with `PrepareBatchExtraInput`.
- For custom callables, return exactly what the selected engine iteration expects.

## Debugging metrics

MONAI handler metrics are Ignite metrics. They collect during iteration and aggregate/reset around epoch boundaries.

- Ensure `output_transform` returns `(y_pred, y)` for metric handlers that need predictions and labels.
- Use `from_engine(["pred", "label"])` for the common supervised output dictionary.
- Check that postprocessing produces tensors/lists in the metric's expected shape and class encoding.
- Avoid using non-scalar metric reductions as key checkpoint metrics unless the saver is configured for a scalar metric.
- Inspect `engine.state.metrics` and `engine.state.metric_details` after evaluator completion.

## Safe fallback pattern

If the environment lacks optional training extras, still help the user progress:

- Keep the data/model/loss/metric code in ordinary PyTorch where possible.
- Explain that MONAI engines and many handlers require Ignite.
- Provide the installation recovery step for the target project environment.
- Offer a tiny CPU smoke script after Ignite is available.
