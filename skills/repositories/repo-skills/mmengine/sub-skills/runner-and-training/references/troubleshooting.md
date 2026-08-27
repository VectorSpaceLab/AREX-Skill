# Runner and Training Troubleshooting

Use this symptom map before changing unrelated model, data, or registry code. Validate config shape with `scripts/runner_config_smoke.py` when the issue looks structural.

## Configuration Completeness

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training fails before first iteration with missing dataloader or loop errors. | `train_cfg` is set but `train_dataloader` is missing or incomplete. | Provide `train_dataloader` and `train_cfg`, or remove training fields for val/test-only workflows. |
| Runner cannot build optimizer wrapper. | `optim_wrapper` is missing, is a raw optimizer dict, or references an unregistered optimizer/constructor. | Use `optim_wrapper=dict(optimizer=dict(type='SGD', ...))`; route registry failures to `configuration-and-registry`. |
| Validation is never run. | Missing `val_cfg`, `val_dataloader`, or `val_evaluator`; `val_interval` too large; `val_begin` later than total training. | Provide all validation fields and align `train_cfg.val_interval` with epoch/iter units. |
| Testing returns no useful metrics. | Missing `test_evaluator` or evaluator returns empty metric dict. | Add a valid evaluator or route metric implementation to `models-metrics-and-inference`. |

## Model Forward and Step Contracts

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training loop errors around `loss`, `parse_losses`, or backward. | `BaseModel.forward(..., mode='loss')` does not return a loss dict, or custom `train_step` does not use `OptimWrapper` correctly. | Route model contract repair to `models-metrics-and-inference`; keep Runner config unchanged until the model step is valid. |
| Validation/test evaluator receives unexpected objects. | `mode='predict'`, `val_step`, or `test_step` output shape does not match metric `process`. | Fix model/evaluator contract in `models-metrics-and-inference`. |
| Multi-optimizer training updates the wrong component. | `OptimWrapperDict` exists but model `train_step` does not select sub-wrappers intentionally. | Implement component-specific update logic in the model workflow. |

## Epoch vs Iter Mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Checkpoints or logs appear at unexpected intervals after converting to iter-based training. | `train_cfg.by_epoch=False` but `CheckpointHook.by_epoch`, `LoggerHook.log_metric_by_epoch`, or `log_processor.by_epoch` stayed epoch-based. | Set checkpoint `by_epoch=False`, logger `log_metric_by_epoch=False`, and `log_processor.by_epoch=False`. |
| Learning rate milestones fire too early or too late. | Scheduler `by_epoch`, `milestones`, `begin`, or `end` units do not match train loop units. | Convert scheduler counts to iterations or set `convert_to_iter_based=True` when preserving epoch-defined milestones. |
| Validation interval is effectively disabled. | `val_interval` is in the wrong unit or larger than `max_epochs`/`max_iters`. | Recompute `val_interval` in the active unit and verify `val_begin`. |

## Checkpoint Best Metric

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Best checkpoint is never saved. | `save_best` metric key does not appear in validation metrics, or validation does not run. | Match `save_best` to evaluator output exactly and ensure validation fields are complete. |
| Best checkpoint comparison goes in the wrong direction. | `rule` is omitted for a custom metric name. | Set `rule='greater'` for accuracy-like metrics or `rule='less'` for loss/error-like metrics. |
| Too many or too few checkpoints remain. | `max_keep_ckpts`, `save_last`, `save_best`, and `interval` interact differently than expected. | Review whether recent periodic checkpoints and best checkpoints are both needed. |
| Published checkpoint is missing expected keys. | `published_keys` excludes optimizer/scheduler/state keys by design. | Use published checkpoints for release/inference, not for training resume. |

## Resume and Load Confusion

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Training restarts at epoch/iter zero after loading weights. | `load_from` was set but `resume=True` was not set. | Use `resume=True` with `load_from` to continue schedule state; use `load_from` alone only for initialization/fine-tuning. |
| Auto resume picks an old checkpoint. | `resume=True` searches the configured `work_dir` for the latest checkpoint. | Use a clean `work_dir` or specify `load_from` with `resume=True`. |
| Optimizer or scheduler state does not match model weights. | Resuming from a checkpoint not saved with optimizer/scheduler state, or loading a published checkpoint. | Resume from a full training checkpoint with optimizer and scheduler state. |

## Hook Ordering and Registration

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Custom hook runs before required runtime fields exist. | Hook priority is too high. | Use default `NORMAL` or a later priority unless the hook intentionally precedes runtime info. |
| Saved optimizer state misses the latest scheduler update. | Checkpoint hook priority was moved earlier than scheduler hook. | Keep checkpoint at very low priority after scheduler updates. |
| Hook registry cannot find a custom hook. | Hook class is not imported/registered in the runtime process. | Register with the hooks registry and ensure project imports occur through config custom imports or application code. |
| Profiler/logging hooks slow training. | Instrumentation hooks are active at high frequency. | Increase intervals, restrict profiling windows, or disable profiler hooks outside diagnosis. |

## OptimWrapper, AMP, and Accumulation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `AmpOptimWrapper` import/build fails. | Optional AMP path conflicts with PyTorch/device support, or wrapper type is misspelled. | Verify PyTorch AMP support and use `type='AmpOptimWrapper'`; fall back to `OptimWrapper` for CPU-safe runs. |
| Loss scale or dtype errors occur. | Unsupported `dtype` or hardware/backend mismatch. | Use `dtype='float16'`, `dtype='bfloat16'`, or default dtype only when the runtime supports it. |
| Gradients update less often than expected. | `accumulative_counts` delays optimizer steps. | Use a positive integer and adjust effective batch size and scheduler assumptions. |
| Gradient clipping has no effect. | `clip_grad` is missing or configured with the wrong norm/value field. | Use `clip_grad=dict(max_norm=...)` or `clip_grad=dict(clip_value=...)` intentionally. |

## Parameter Scheduler Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Scheduler hook raises a type assertion. | `runner.param_schedulers` is neither a scheduler, a list, nor a dict containing scheduler lists. | Make `param_scheduler` a dict or list of dicts in config-driven Runner usage. |
| Warmup overlaps the main scheduler unexpectedly. | `begin`/`end` intervals overlap or leave gaps unintentionally. | Use adjacent `[begin, end)` intervals and document intentional overlap. |
| Resume changes LR unexpectedly. | Scheduler state was not resumed or scheduler config changed between runs. | Resume from full checkpoints and avoid changing scheduler definitions mid-run. |

## Distributed and Strategy Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Distributed job hangs at startup. | Launcher, rank environment, master address/port, or backend is wrong. | Use `torchrun` or scheduler-provided launch variables; match Runner `launcher`; try `gloo` for CPU checks and `nccl` for CUDA. |
| `DefaultSampler` shuffling repeats in distributed training. | `DistSamplerSeedHook` was removed or custom sampler lacks epoch seed updates. | Restore `DistSamplerSeedHook` or implement equivalent sampler seed updates. |
| `DeepSpeedStrategy`, `FSDPStrategy`, or `ColossalAIStrategy` cannot import. | Optional packages or hardware-specific dependencies are absent. | Treat these as dependency/hardware-gated paths; install compatible optional packages or choose standard Runner/AMP. |
| FSDP or strategy checkpoint load fails. | Strategy-specific state dict format or sharding configuration changed. | Keep strategy configuration stable across save/resume and verify state dict type compatibility. |
| `torch.compile` fails before training. | Model code uses unsupported dynamic behavior or PyTorch compile backend limitations. | Disable compile or choose conservative compile options; route model graph changes to `models-metrics-and-inference`. |

## Safe Triage Steps

1. Reduce the config to the intended workflow: train-only, train+val, val-only, or test-only.
2. Run the bundled smoke helper on a JSON representation of the Runner fields.
3. Align loop units across `train_cfg`, hooks, log processor, and schedulers.
4. Confirm checkpoint semantics before changing `work_dir`, `load_from`, or `resume`.
5. Route non-Runner contract issues to the owning sibling skill instead of patching around them in hooks.
