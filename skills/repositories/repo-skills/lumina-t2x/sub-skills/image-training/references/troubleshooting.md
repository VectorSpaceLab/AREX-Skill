# Image Training Troubleshooting

## Purpose

Use this page when a Lumina image training run fails before or during distributed startup.

## FlashAttention import failure

**Symptoms**
- `ModuleNotFoundError: No module named 'flash_attn'`
- The trainer cannot even import the model module.

**Likely cause**
- The private environment does not have a compatible FlashAttention build.

**Recovery**
- Install a CUDA-compatible FlashAttention build before relaunching training.
- Re-run the shared environment checker with `--workflow image-training`.

## Apex norm failure

**Symptoms**
- `No module named 'fused_layer_norm_cuda'`
- A training run crashes around fused RMSNorm or Apex normalization.

**Likely cause**
- A Python-only Apex build was installed instead of a full CUDA+C++ build.

**Recovery**
- Remove the broken Apex install or replace it with a full build.
- If Apex is optional for the selected workflow, leave it out and use the vanilla path.

## Distributed launch problems

**Symptoms**
- `nccl` startup errors.
- The run hangs before the first batch.
- `torchrun` or Slurm starts with the wrong number of GPUs.

**Likely cause**
- The launch command does not match the selected data-parallel strategy or available hardware.

**Recovery**
- Use the repo's distributed launch pattern exactly as written in the workflow reference.
- Verify that the local environment sees the requested CUDA devices before starting a long run.

## Stale or wrong data cache

**Symptoms**
- The trainer appears to ignore recent manifest edits.
- The same samples keep reappearing after the manifest changes.

**Likely cause**
- `accessory_data_cache/` still contains a cache derived from an older config.

**Recovery**
- Delete the cache directory derived from the config path and rerun the job.
- Re-run `scripts/check_training_data.py` to confirm the manifest points at the current files.

## Checkpoint resume / init confusion

**Symptoms**
- Resume picks up the wrong optimizer state.
- Finetuning behaves like a fresh run or vice versa.

**Likely cause**
- `--resume` and `--init_from` were swapped.

**Recovery**
- Use `--resume` only when you want optimizer and loader state restored.
- Use `--init_from` only when you want weights without the full training state.

## Offline model loading failures

**Symptoms**
- The trainer tries to download diffusers models from the internet.
- Offline environments fail during `from_pretrained` calls.

**Likely cause**
- `--local_diffusers_model_root` was not set in an offline environment.

**Recovery**
- Point `--local_diffusers_model_root` at a local mirror before retrying.
