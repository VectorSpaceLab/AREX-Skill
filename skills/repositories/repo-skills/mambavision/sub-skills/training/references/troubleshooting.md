# MambaVision training troubleshooting

Use this guide after a failed launch or when the first debug run does not behave as expected.

## Fast triage order

1. Run `python <training-entrypoint> --help` to verify the parser and imports.
2. Confirm the dataset root and split names.
3. Retry on a single GPU with a small batch size.
4. Re-enable distributed launch only after the single-GPU path works.

## Common failures

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| `Training folder does not exist at:` | `--data_dir` points at the wrong root or the `train/` split is missing. | Point `--data_dir` at the dataset root and verify `train/` exists. |
| `Validation folder does not exist at:` | The validation split name does not match the on-disk folder. | Rename the folder or change `--val-split` to `val`. |
| ImageNet/LMDB mismatch | You enabled the LMDB branch but the root tree does not match the expected ImageFolder cache layout. | Make the dataset root consistent, then regenerate or reuse the matching cache files. |
| CUDA OOM | Batch size, validation batch size, or input size is too large for the chosen model. | Lower `--batch-size` first, then `--validation-batch-size`; keep `--amp` on while debugging memory. |
| Host RAM pressure or slow loader startup | Too many dataloader workers for the machine. | Lower `--workers`. |
| DDP/NCCL hang or init failure | `torchrun` world size, GPU visibility, or Slurm env vars are inconsistent. | Use `torchrun --standalone` on one node, keep `CUDA_VISIBLE_DEVICES` aligned, and ensure one process per GPU. |
| `WORLD_SIZE` accidentally triggers distributed mode | Leftover distributed env vars from a previous job. | Unset stale env vars or launch from a clean shell. |
| AMP warning or fallback | Native AMP or Apex is missing. | Use `--native-amp` if supported, or install the backend you want; `--amp` chooses the best available backend automatically. |
| W&B is not logging | `wandb` is optional and not installed. | Install `wandb` or omit `--log-wandb`. |
| TensorBoard import/logging failure | `tensorboardX` is missing or the log root is not writable. | Install `tensorboardX` and point `--log_dir` at a writable location. |
| Resume does not restore the same run | `--resume` was confused with `--initial-checkpoint`. | Use `--resume` for the full state, `--initial-checkpoint` for weights only. |
| EMA weights look missing | The checkpoint did not contain EMA state or `--model-ema` was not enabled. | Keep `--model-ema` on when you expect EMA evaluation, and resume with a checkpoint that includes EMA weights. |
| `Nan in loss, exit` | The training loop detected an unstable loss. | Lower the learning rate, reduce `--mesa`, disable mixup/cutmix temporarily, and test without AMP to isolate the source. |

## Memory and precision notes

- `--channels-last` is a performance hint, not a cure-all. Keep it enabled on CUDA unless it exposes a backend-specific issue.
- If OOM persists after lowering batch size, try a smaller model, a smaller input size, or a smaller validation batch size.
- `--amp` prefers native AMP first and Apex second. If you need to test a specific path, force `--native-amp` or `--apex-amp`.
- `--bfloat` switches the training dtype to bfloat16 when the script path supports it; use it cautiously and only on compatible hardware.

## Distributed and Slurm notes

- The script enters distributed mode when `WORLD_SIZE` is greater than 1.
- `torchrun` is the safest way to set `WORLD_SIZE` and `LOCAL_RANK` for local multi-GPU work.
- On Slurm, make sure the launcher does not fight with `torchrun` over rank assignment.
- If NCCL hangs, check that the visible GPU count matches the requested process count and that the chosen port is free.
- If SyncBatchNorm is not required, leave `--sync_bn` off while debugging.
- `--no-ddp-bb` can help with broadcast-buffer issues in some native DDP setups.

## Data layout problems

- If the run reports a missing validation folder, first check whether the tree uses `validation/` or `val/`.
- If the run reports a missing training folder, check whether `--data_dir` accidentally points at `.../train` instead of the dataset root.
- If you are using the LMDB branch, do not point the loader at a partial split directory.
- A stale cache is a common reason for the wrong labels or wrong sample count after a data refresh.

## Checkpoint semantics

- `--resume` restores the optimizer and scaler state when present.
- `--initial-checkpoint` only seeds the model weights.
- `--loadcheckpoint` partially loads matching tensors by shape and is useful when the architecture changed.
- `--no-resume-opt` skips optimizer state restoration during resume.
- EMA checkpoints are loaded separately from the base model when `--model-ema` is active.

## NaN and anomaly debugging

When the script prints `Nan in loss, exit`, it also replays a forward pass under anomaly detection and prints the output.
Most common root causes:
- learning rate too high for the selected batch size
- an overly strong `--mesa` setting
- a bad checkpoint or partially compatible transfer load
- unstable data augmentation
- mixed-precision overflow

Suggested isolation sequence:
1. cut the learning rate
2. disable `--mesa`
3. turn off `--mixup` and `--cutmix` temporarily
4. test one GPU with a tiny batch size
5. switch off AMP only long enough to confirm whether the issue is numeric

## Logging issues

- TensorBoard scalars are written through `tensorboardX`.
- The log directory name is assembled from `--log_dir` plus the tag, so choose a clean `--log_dir` root.
- W&B only activates when `--log-wandb` is passed and the package is installed.
