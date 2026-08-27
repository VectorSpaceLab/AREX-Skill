# Training Troubleshooting

## CUDA and import failures

If the command fails before parsing flags with:

```text
AssertionError: You need to have an Nvidia GPU with CUDA installed.
```

use the root [cross-cutting troubleshooting](../../../references/troubleshooting.md).
This package cannot even import its main module in a CPU-only environment.

## Empty or unsupported data folder

**Symptom**

```text
No images were found in <folder> for training
```

**Likely causes**

- `--data` points to the wrong folder.
- The folder has no `.jpg`, `.jpeg`, or `.png` files.
- Images are in another archive or unsupported format.

**Recovery**

- Check the recursive file count:
  ```bash
  find /path/to/images -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | head
  ```
- Convert or copy a small subset to a smoke folder before long training.
- Generate a synthetic fixture with `scripts/make_tiny_fixture.py` only for
  command/CUDA smoke tests, not for quality evaluation.

## Invalid image size

**Symptom**

```text
image size must be a power of 2 (64, 128, 256, 512, 1024)
```

**Recovery**

Use a power-of-two `--image_size`. For smoke testing, `64` is usually enough;
for final training choose the resolution that matches the user's data and GPU
memory.

## Out of memory or slow training

**Symptoms**

- CUDA out-of-memory traceback.
- The first evaluation/checkpoint takes too long.
- GPU memory pressure when attention, feature quantization, high resolution, or
  large batch size is enabled.

**Recovery order**

1. Lower `--batch_size`.
2. Increase `--gradient_accumulate_every` to preserve effective batch size.
3. Lower `--network_capacity` if necessary.
4. Test at smaller `--image_size` first.
5. Disable optional memory-heavy flags (`--attn_layers`, `--fq_layers`,
   `--cl_reg`, `--top_k_training`) until the base run is healthy.

## NaNs and divergence

The CLI wraps each training step with retries for `NanException`. If NaNs keep
reappearing:

- Resume from the last stable checkpoint if available.
- Reduce learning rate or model capacity.
- Enable or adjust augmentation for low-data training.
- Inspect whether the dataset is too small, duplicated, corrupt, or too
  homogeneous.
- Treat final GAN quality as a training/experiment issue rather than a CLI
  syntax issue.

## Resume loads the wrong run or no run

**Symptoms**

- `continuing from previous epoch - <n>` names an unexpected checkpoint.
- Generation says no outputs were produced or silently returns after no
  checkpoint exists.
- Loading fails with a model shape mismatch.

**Recovery**

- Verify the exact `--models_dir` and `--name` used for the previous run.
- Use `--load_from <n>` for a specific checkpoint.
- Use `--new` only when intentionally discarding the run's current outputs and
  checkpoints.
- If architecture settings changed, do not expect an old checkpoint to load;
  start a new run or restore the old settings from `.config.json`.

## List flag parsing problems

List flags should not contain shell-expanded spaces. Prefer quoting:

```bash
stylegan2_pytorch --data /path/to/images --attn_layers '[1,2]'
stylegan2_pytorch --data /path/to/images --aug_types '[translation,cutout,color]'
stylegan2_pytorch --data /path/to/images --fq_layers '[1,2]'
```

If Fire rejects a hyphenated flag, retry the underscore spelling from
`stylegan2_pytorch -- --help`.

## Optional dependency and service failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Apex is not available` | `--fp16` requested without Apex | Disable `--fp16` or install Apex for the exact CUDA/PyTorch stack. |
| `ModuleNotFoundError: pytorch_fid` | FID enabled without `pytorch-fid` | Install `pytorch-fid` only when FID is needed. |
| Aim logging works but no dashboard | `--log` only creates a session; UI service not running | Start/manage Aim UI separately if the user has Docker/service access. |
| Assertion about contrastive regularization and transparent images | `--cl_reg` with `--transparent` | Disable one of the two. |
| Assertion about contrastive regularization and multi-GPU | `--cl_reg` with DDP | Disable `--cl_reg` for multi-GPU. |

## Multi-GPU hangs or NCCL errors

- Confirm more than one CUDA device is visible with `nvidia-smi`.
- Restrict devices explicitly with `CUDA_VISIBLE_DEVICES=0,1`.
- Keep `--gradient_accumulate_every 1` for the README-style multi-GPU recipe
  unless the user has reason to tune it.
- Avoid `--cl_reg` with multi-GPU.
- If NCCL or process-group initialization fails, verify the PyTorch CUDA/NCCL
  install before debugging StyleGAN-specific flags.
