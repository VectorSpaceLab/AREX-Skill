# Troubleshooting

## Purpose

Read this when HunyuanVideo-I2V fails to install, import, find checkpoints, or validate its data/layout assumptions.

## 1) Runtime install conflict: `tokenizers` vs `transformers`

**Symptom**

- `ResolutionImpossible`
- A message saying `transformers 4.48.0` requires `tokenizers>=0.21,<0.22` while an older pin asks for `tokenizers==0.15.0`

**Cause**

An old requirements file pins a tokenizers release incompatible with the inspected transformers pin.

**Recovery**

- Start from the checkout root and install `requirements.txt`, which pins the verified pair `transformers==4.48.0` and `tokenizers==0.21.0`.
- The same base file includes `decord==0.6.0` and `omegaconf==2.3.0`, which are direct HyVAE imports.
- Install `requirements-optional.txt` only for a matching CUDA/DeepSpeed, flash-attention, or xDiT workflow; do not add those GPU packages to a CPU-only environment.
- Re-run `python -m pip check` after the install.

## 2) `torch` import fails with `iJIT_NotifyEvent`

**Symptom**

- `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`

**Cause**

A broken or mismatched PyTorch/CUDA runtime stack.

**Recovery**

- Replace the broken torch stack with a CUDA 12.4 wheel set that matches `torch==2.4.0+cu124`.
- Verify `import torch` and a CUDA tensor allocation before trying flash-attn or model imports.

## 3) flash-attn build fails

**Symptom**

- `OSError: CUDA_HOME environment variable is not set`
- nvcc not found
- flash-attn metadata build fails during `pip install`

**Cause**

The source build cannot find a CUDA toolkit compiler path.

**Recovery**

- Install a CUDA compiler tool into the env, such as `cuda-nvcc=12.4.99`.
- Set `CUDA_HOME` to the env prefix before installing flash-attn.
- Re-run the build with `MAX_JOBS` kept small.

## 4) Missing checkpoints or model assets

**Symptoms**

- `ValueError: \`models_root\` not exists`
- `AssertionError: VAE checkpoint not found`
- `No model weights found` / `model_path not exists`

**Cause**

`ckpts/` does not contain the required transformer, VAE, or text-encoder folders.

- Read [`references/checkpoints.md`](checkpoints.md).
- Run the checkpoint helper from the checkout root, for example `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference`.
- Download the public checkpoint tree before trying real generation or training; the skill does not fabricate or bundle weights.

## 5) Inference argument errors

**Symptoms**

- `video_length-1 must be a multiple of 4`
- invalid `i2v_resolution`
- invalid `i2v_condition_type`
- `Number of GPUs should be equal to ring_degree * ulysses_degree`
- image resolution not divisible by the sequence-parallel degree

**Cause**

The inference CLI and sampler enforce shape and parallelism constraints.

**Recovery**

- Use `video_length` values like `129`.
- Keep `i2v_resolution` in `{360p, 540p, 720p}`.
- Ensure the xDiT product matches the active GPU count.
- If xDiT asks for image resizing, set `ALLOW_RESIZE_FOR_SP=1` only when you accept the resize.

## 6) LoRA training fails before the first update

**Symptoms**

- Missing `--task-flag` or `--output-dir`
- Invalid `--data-jsons-path`
- DeepSpeed errors about batch-size divisibility or distributed init
- `FileNotFoundError` when loading the base transformer, VAE, or text encoders

**Cause**

The launcher expects a preprocessed dataset and the same checkpoint tree used for inference.

**Recovery**

- Generate latents first with the data-preparation sub-skill.
- Check the checkpoint tree.
- Use the bundled training wrapper in dry-run mode to inspect the final deepspeed command before you execute it.

## 7) Latent extraction or dataset validation fails

**Symptoms**

- `meta_file.list` not found
- `video_path` or caption JSON missing fields
- extraction skips everything because cached `.npy` files already exist
- `decord` cannot open the video path

**Cause**

The raw metadata format or the target output layout is wrong.

**Recovery**

- Read [`sub-skills/data-preparation/references/data-formats.md`](../sub-skills/data-preparation/references/data-formats.md).
- From the checkout root, validate raw metadata with `python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode raw --meta-file-list ...`.
- Ensure the processed latent JSON references a real `.npy` path.

## 8) Optional xDiT / `xfuser` missing

**Symptom**

- Multi-GPU inference branches are unavailable, but single-GPU inference still works.

**Cause**

`xfuser` is optional and was not installed.

**Recovery**

- Install `xfuser==0.4.0` only if you need xDiT sequence-parallel inference.
- Leave it uninstalled for single-GPU sampling or when you want a smaller inspection environment.

## Next Checks

Run these helpers from the real checkout root; `$SKILL_ROOT` points to the generated skill directory and `$CHECKOUT_ROOT` points to the checkout:

- `$SKILL_ROOT/scripts/check_runtime.py`
- `$SKILL_ROOT/scripts/check_checkpoint_layout.py`
- `$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py`
- the relevant sub-skill `SKILL.md`
