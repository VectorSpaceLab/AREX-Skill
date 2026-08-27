# Experiment Artifacts

## Purpose

Read this when deciding whether a training experiment started, finished, failed, or produced enough files for prompting/export. Paths below are relative to the configured `output_directory` of a single experiment.

## Core files and directories

| Artifact | Written by | Meaning |
|---|---|---|
| `cfg.yaml` | training process rank 0 | Resolved config saved before and after training. Use it to confirm CLI overrides and GUI-derived settings. |
| `flags.json` | direct trainer or Wave launcher | Status and short info. `finished` means the trainer reached normal postprocessing. `running` means Wave-launched work has started. `failed` means inspect `info` and `logs.log`. |
| `flags<N>.json` | Wave-launched multi-rank failures | Per-rank failure status. The app aggregates these and prefers detailed error info over generic `See logs`. |
| `logs.log` | experiment logger | Main human-readable training log for rank 0, or all ranks when all-rank logging is enabled. |
| `charts_cache/` | local logger | Disk cache backing Charts UI: train/validation metrics, learning rate, config summary, internal step counts, and plot data. |
| `checkpoint.pth` | checkpoint saver | Main model state dict. With DeepSpeed ZeRO, rank 0 gathers or reconstructs a normal checkpoint when possible. |
| `adapter_model/` | checkpoint saver | Saved PEFT adapter directory when LoRA is enabled and no LoRA unfreeze layers are used. |
| `classification_head.pth` | checkpoint saver | Classification head weights for classification experiments when present. |
| `regression_head.pth` | checkpoint saver | Regression head weights for regression experiments when present. |
| `validation_predictions.csv` | prediction saver | Postprocessed validation predictions for inspection/export. |
| `validation_raw_predictions.pkl` | prediction saver | Raw validation prediction outputs. |
| `preds_<experiment_name>.zip` | postprocessing helper | Zip containing validation prediction files, created after normal direct training completion. |
| `charts_<experiment_name>.json` and `logs_<experiment_name>.zip` | export/log helper | Log/chart export material produced by the app/export path rather than by every direct CLI run. |

## Status interpretation

1. `flags.json` missing and no `logs.log`: the process may not have reached training setup. Check Python imports, DeepSpeed/CUDA initialization, wrong working directory, or a bad command.
2. `flags.json` status `running`: a Wave-launched process has started. Inspect process liveness and `logs.log` for progress.
3. `flags.json` status `finished`: training/evaluation postprocessing reached the end. Confirm expected files still exist; a zero-epoch evaluation can finish without the same training curves as a full run.
4. `flags.json` status `failed`: inspect `info` first, then `logs.log`, then per-rank `flags<N>.json` for distributed failures.
5. `flags.json` status absent or unexpected: treat as incomplete and inspect command stderr/stdout plus `logs.log`.

## Checkpoint modes

`training.save_checkpoint` controls when checkpoint files are written:

- `last`: save the last checkpoint in the output directory; this is the recommended default in the user docs.
- `best`: save when the validation metric improves; useful but can overfit validation if used as a substitute for tuning.
- `each_evaluation_epoch`: save a checkpoint folder per evaluation epoch; useful for debugging and consumes more disk.
- `disable`: skip checkpoints; useful for debugging disk usage but disables downstream chat/export workflows that need trained weights.

When `training.epochs` is `0` and checkpoint saving is not disabled, the trainer still evaluates and saves a checkpoint of the loaded model.

## Charts and logs

The local logger always writes `charts_cache/` for the app's charts and comparison views. The cache can include config summaries, training loss, validation loss/metric, learning rate, validation plots, and internal step counts.

`logging.logger: W&B` enables external Weights & Biases logging. If W&B initialization fails, H2O LLM Studio logs a warning and disables external logging while keeping local artifacts. The config checker rejects W&B with `logging.log_step_size: relative`; use `absolute` for W&B.

## Distributed artifact notes

- Rank 0 owns the main `cfg.yaml`, `logs.log`, predictions, and normal `flags.json` completion.
- With distributed inference enabled, validation predictions are synchronized across GPUs before rank 0 postprocesses them.
- If one rank fails under the Wave launcher, inspect `flags<N>.json` and `logs.log`; a non-rank-0 failure can otherwise look like a generic distributed shutdown.
- DeepSpeed ZeRO checkpoint conversion can take time and disk space because rank 0 may gather/reconstruct full weights for `checkpoint.pth`.

## Export handoff

For interactive chat, Hugging Face publishing, model-card artifacts, or checking whether an experiment directory is usable for export, route to `../export-and-prompt/SKILL.md`. Training only guarantees the training-side artifacts above; publish/export commands add their own credential, network, and serialization requirements.
