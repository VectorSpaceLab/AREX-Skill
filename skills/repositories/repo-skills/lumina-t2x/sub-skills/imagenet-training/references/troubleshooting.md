# ImageNet Training Troubleshooting

## Purpose

Use this page when an ImageNet benchmark run fails before or during the first distributed step.

## FlashAttention or Apex problems

**Symptoms**
- `ModuleNotFoundError: No module named 'flash_attn'`
- `No module named 'fused_layer_norm_cuda'`
- Model import fails before training begins.

**Likely cause**
- The environment is missing a compatible FlashAttention build or has a broken Apex install.

**Recovery**
- Install a CUDA-compatible FlashAttention build.
- Remove a Python-only Apex build or replace it with a full CUDA+C++ build.
- Re-run the shared environment checker with `--workflow imagenet`.

## Dataset layout problems

**Symptoms**
- The training script cannot find the ImageNet train/val folders.
- The run fails after the shell script starts but before the first batch.

**Likely cause**
- `train_data_root` still points at the placeholder path.
- The dataset root does not match the expected class-folder layout.

**Recovery**
- Validate the dataset tree with `scripts/check_imagenet_layout.py`.
- Edit the `train_data_root` line in the stage script before relaunching.

## GPU-count mismatch

**Symptoms**
- The launch completes on the wrong number of devices or exits early.
- A large model asks for more GPUs than the current node provides.

**Likely cause**
- The chosen `exps/*.sh` or Slurm wrapper does not match the available cluster size.

**Recovery**
- Follow the repository's single-node or Slurm template exactly.
- Use the model size warning in the README as the guide for whether a larger cluster is required.

## Checkpoint or class-label issues

**Symptoms**
- Sampling fails because the checkpoint folder is incomplete.
- The class labels do not match the intended benchmark run.

**Likely cause**
- The wrong checkpoint directory was passed to `sample.py`.
- The sampling command used the wrong set of class labels.

**Recovery**
- Verify the checkpoint tree and the sampling labels before launching again.
