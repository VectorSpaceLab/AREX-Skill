# Troubleshooting

## Purpose

Read this when a training run fails to start or crashes during launch.

## `.cuda()` or CUDA runtime failures

### Symptoms
- `RuntimeError` when the model or batch is moved to CUDA.
- `Could not find cuda drivers on your machine`.
- `CUDA not available` on a host that was expected to have a GPU.

### Cause
- The environment has CPU-only PyTorch or a driver/wheel mismatch.

### Recovery
- Confirm the CUDA smoke helper passes before launching training.
- Do not silently switch a GPU-required training task to CPU when the source script is written for CUDA.

## Multi-GPU launch problems

### Symptoms
- NCCL or distributed initialization errors.
- Multiple workers hang during startup.
- `WORLD_SIZE` or `local_rank` settings do not match the GPU count.

### Cause
- The launcher and environment variables are inconsistent.
- The host does not expose the number of GPUs that the launcher expects.

### Recovery
- Use the bundled launcher template and set the visible device list explicitly.
- Verify the number of GPUs before choosing a distributed launch.

## Checkpoint and resume problems

### Symptoms
- Resume loads the wrong epoch or fails to find the checkpoint.
- `optimizer` state is missing from the checkpoint.
- Fine-tuning does not load the expected backbone weights.

### Cause
- The checkpoint filename does not match the repo's `ep%03d.pth` assumption.
- The user gave a checkpoint from a different training setup.

### Recovery
- Use the repo's checkpoint naming convention.
- Distinguish `resume` from `finetune`: resume expects optimizer state, finetune only reuses backbone weights.

## Auto-backup copies too much

### Symptoms
- Training appears to stall while copying files.
- The log directory contains a huge backup tree.

### Cause
- `auto_backup` is on and `log_path` points inside or near the repo tree.

### Recovery
- Put logs outside the repository tree.
- Disable `auto_backup` unless the user explicitly wants a code snapshot.

## Backbone and shape mismatches

### Symptoms
- The model loads but produces shape errors or obviously wrong predictions.

### Cause
- `backbone`, `griding_num`, `num_lanes`, or `use_aux` do not match the dataset family or checkpoint.

### Recovery
- Re-read `data-and-config` for the correct dataset-specific dimensions.
- Keep the training command aligned with the checkpoint and dataset family.

## Warning-only issues

- Modern `torchvision` may warn that `pretrained` is deprecated. This is a compatibility warning in this repo, not the main cause of a training failure.
