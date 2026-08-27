# Training Troubleshooting

## Training crashes immediately on `.cuda()`

Cause: the native training scripts require CUDA and do not have a CPU fallback.

Recovery:

- Verify CUDA with the root `check_environment.py --expect-cuda yes` helper.
- Select a CUDA-capable PyTorch build for the host driver.
- If no CUDA backend is available, restrict work to config validation and do not claim training verification.

## Out-of-memory during training

Likely causes:

- Batch size too large for available GPUs.
- Too many data loader workers or pinned-memory pressure.
- Running refine/base settings on fewer GPUs than the original setup.

Recovery:

- Reduce `--batch` in the bundled runner.
- Lower `--workers` when CPU/RAM pressure is high.
- Limit `CUDA_VISIBLE_DEVICES` deliberately with `--gpu` rather than relying on all visible GPUs.
- Keep experiment logs and snapshots separate per run.

## Dataset root or annotation JSON missing

Symptoms: file-not-found errors after data loader construction, missing `crop511`, missing `train.json`, or empty datasets.

Recovery:

1. Run the data-preparation layout checker with `--dataset training`.
2. Run the training helper in dry-run mode and inspect the config summary.
3. Prepare missing COCO/DET/VID/YouTube-VOS crop/index files before starting training.

## `resnet.model` or base checkpoint is missing

Training from scratch/refine depends on external pretrained files.

Recovery:

- Confirm whether the selected workflow needs backbone `resnet.model`, a base SiamMask checkpoint, or a resume checkpoint.
- Resolve paths relative to the selected experiment directory or use absolute paths.
- Do not start network downloads without user approval.

## Resume starts at the wrong epoch or optimizer state fails

Cause: `--resume` restores both model and optimizer state and expects checkpoint metadata such as `epoch`, `best_acc`, `arch`, and optimizer parameters.

Recovery:

- Use `--pretrained` when only weights are intended.
- Use `--resume` only for checkpoints saved by matching SiamMask training scripts.
- Match `--start-epoch` to the checkpoint's epoch when resuming.

## Refine training produces poor masks

Likely causes:

- Wrong or weak base checkpoint passed as `--pretrained`.
- Dataset mix missing COCO/YouTube-VOS masks.
- Downstream evaluation omitted `--mask --refine` or used a VOT config that does not match the checkpoint.

Recovery:

- Validate mask-capable data paths.
- Confirm refine config uses mask-focused loss weights.
- Test a small benchmark run with the tracking sub-skill before launching broad evaluation.

## Exact legacy dependencies are unavailable

Do not force old pins into an incompatible modern Python. Use a compatible environment for operational work and record that exact historical reproduction requires a matching legacy stack.
