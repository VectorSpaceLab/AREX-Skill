# LaneNet Training Troubleshooting

Use this reference when training fails, produces no checkpoints, or diverges. Keep fixes scoped to training; route data generation to `../data-preparation/`, inference to `../inference-evaluation/`, and export to `../model-export/`.

## Quick triage order

1. Validate the repository root and working directory. The config loader is repo-root-relative and the shipped config contains `REPO_ROOT_PATH` placeholders.
2. Validate the prepared TFRecords. Training needs at least the train set, and multi-GPU validation also needs the val set.
3. Validate the GPU mode. The validated training path is TensorFlow 1.15 + CUDA.
4. Validate the backbone and checkpoint compatibility. `MODEL.FRONT_END` and `MODEL.EMBEDDING_FEATS_DIMS` must match the checkpoint.
5. Validate the batch size against the number of records and the number of GPUs before starting the run.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Config file ... can not be read` or paths still contain `REPO_ROOT_PATH` | Training was started from the wrong directory, or the wrapper was skipped and the placeholder paths were never resolved. | Run from the repository root or use the bundled wrapper with `--repo_root`; it resolves `REPO_ROOT_PATH` automatically. |
| `.../tfrecords not exist` | Dataset preparation or TFRecord generation has not been completed, or `DATASET.DATA_DIR` points at the wrong root. | Route the missing conversion step to `../data-preparation/`, then point `DATASET.DATA_DIR` at the prepared data root. |
| No checkpoints are written after a tiny run | `steps_per_epoch <= 1`, usually because `BATCH_SIZE` is too large for the number of TFRecords. The source loop iterates `range(1, steps_per_epoch)`, so a one-step epoch produces no training step. | Lower `TRAIN.BATCH_SIZE` or add more TFRecords until `steps_per_epoch > 1`. The bundled wrapper refuses this case before training starts. |
| Validation logs never appear in multi-GPU mode | Validation TFRecords are missing or `VAL_BATCH_SIZE` is too large for the val set. | Prepare the val TFRecords and lower `TRAIN.VAL_BATCH_SIZE` until at least one full validation batch exists. |
| `ValueError` or crash around `gpu:1` | Multi-GPU config names more devices than are visible, or the batch size is smaller than the GPU count. | Align `TRAIN.MULTI_GPU.GPU_DEVICES` with the visible CUDA devices, or set `TRAIN.MULTI_GPU.ENABLE=False` for a single-GPU run. |
| Batch size works on one GPU but not on multiple GPUs | The multi-GPU trainer splits the batch with integer division. Non-divisible batches are rounded down; if the batch size is smaller than the number of devices, per-GPU batch becomes zero. | Make `TRAIN.BATCH_SIZE` divisible by the GPU count, or reduce the number of devices. |
| `NotFoundError`, missing variable, or shape mismatch during restore | Checkpoint/front-end mismatch, wrong embedding dimension, or a bad snapshot path. | Keep `MODEL.FRONT_END` and `MODEL.EMBEDDING_FEATS_DIMS` aligned with the checkpoint. Pass the checkpoint base path, not a shard filename. |
| Restore was enabled but the run silently started from scratch | The source trainer falls back to scratch when restore fails. | Use the bundled wrapper so the missing snapshot is caught before training, or disable `TRAIN.RESTORE_FROM_SNAPSHOT.ENABLE` explicitly if scratch training is intended. |
| CUDA OOM | Batch size is too large, too many GPUs/processes are contending, or the memory fraction is too high for the host. | Lower `TRAIN.BATCH_SIZE`, reduce `GPU.GPU_MEMORY_FRACTION`, keep `GPU.TF_ALLOW_GROWTH=True`, or use one GPU. |
| Loss becomes NaN or training becomes unstable | Learning rate is too aggressive, labels are corrupted, or the optimizer choice is unstable for the current data. The README notes that SGD is more stable than Adam. | Keep `SOLVER.OPTIMIZER=sgd`, lower `SOLVER.LR`, verify label quality, and consider freezing BN if the graph remains unstable. |
| `AttributeError: ... _warmup_init_learning_rate` during graph construction | The upstream trainer still traces the warm-up branch even when warm-up is disabled. | Keep `TRAIN.WARM_UP.ENABLE=True` and shorten the run with smaller `TRAIN.EPOCH_NUMS` and `TRAIN.BATCH_SIZE`, or patch the trainer before trying to disable warm-up. |
| TensorFlow import fails with protobuf errors | TensorFlow 1.15 is sensitive to protobuf 4.x. | Use `protobuf<=3.20.x`; the verified environment uses `3.20.3`. |
| Log file or TensorBoard directory is missing | `LOG.SAVE_DIR` is not writable or was removed. | Create the directory before launching training, or use the bundled wrapper, which creates the log directory for you. |
| `Train miou` stays missing in logs | `TRAIN.COMPUTE_MIOU.ENABLE=False`, or the run never reaches a valid training step. | Enable `TRAIN.COMPUTE_MIOU.ENABLE` and make sure the training loop actually has at least one batch to process. |
| GPU is not visible on a newer host or driver stack | The validated path is still TF 1.15 + CUDA / cuDNN. Newer accelerator setups are not guaranteed to work without a compatible CUDA 10-era runtime. | Confirm the TensorFlow GPU build sees a device, and treat modern driver or accelerator combinations as generic compatibility work rather than a repo bug. |

## Missing pretrained weights

The repository documentation discusses external pretrained weights, but this generated skill does not bundle them. When a user asks for pretrained training or resume behavior without a local checkpoint:

1. State that a local checkpoint is required.
2. Ask them to provide the checkpoint directory or base path after downloading weights outside the skill.
3. If they want to create weights, route the request to `../training/`.
4. Do not fabricate model filenames or imply that weights are included in the generated skill tree.

## Output directory checks

| Directory | Expected contents |
| --- | --- |
| `LOG.SAVE_DIR` | `lanenet_train_*.log` from the wrapper and the trainers. |
| `TRAIN.MODEL_SAVE_DIR/<front_end>_lanenet/` | TensorFlow checkpoint shards and `.ckpt-*` snapshots. |
| `TRAIN.TBOARD_SAVE_DIR/<front_end>_lanenet/` | TensorBoard event files and `model_train_config.json`. |

If the model or TensorBoard directories do not appear, check whether the run ever reached a valid training step, and confirm that the output path is writable.
