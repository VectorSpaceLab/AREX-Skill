# Multi-GPU Guidance

## Purpose

Use this file when adapting MinkowskiEngine's multi-GPU examples or diagnosing distributed training setup.

## Requirements

A multi-GPU workflow needs all of the following:

- A CUDA-enabled MinkowskiEngine build.
- A torch CUDA build with visible devices.
- Multiple GPUs or a launch configuration that matches the host.
- Any framework extras such as PyTorch Lightning when using the Lightning example family.

Do not treat a CPU-only build as ready for multi-GPU verification.

## DDP Pattern

The repo examples use standard PyTorch distributed data parallel ideas:

1. Build a dataset that returns coordinate/feature/label rows.
2. Collate rows into batched coordinates with `ME.utils.sparse_collate`.
3. Construct `ME.SparseTensor` inside the process that performs the forward pass.
4. Wrap the model with DDP after device assignment.
5. Periodically clear CUDA cache when sparse batch sizes vary significantly.

## Lightning Pattern

The Lightning example wraps these parts in a `LightningModule`:

- model and optimizer configuration,
- `train_dataloader` and `val_dataloader`,
- `training_step` and `validation_step`,
- sparse tensor construction from collated coordinates/features.

Use Lightning only when that framework is already part of the user's stack.

## Memory and Cache Notes

Sparse tensors have variable numbers of active coordinates per batch. A later batch can require a larger allocation than earlier batches. The repo examples use periodic `torch.cuda.empty_cache()` to reduce repeated allocation pressure.

## Safe Verification

For this generated skill, multi-GPU examples are reference-only. Verify a CUDA build and a tiny single-process smoke first, then choose a small distributed smoke before running real training.

## Stop Conditions

Stop and return to `build-and-install` if:

- `ME.is_cuda_available()` is false.
- torch CUDA is unavailable.
- the build was compiled with `CPU_ONLY`.
- the host lacks multiple devices for the requested launch.
