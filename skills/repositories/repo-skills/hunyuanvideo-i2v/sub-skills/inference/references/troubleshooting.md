# Inference Troubleshooting

## Purpose

Read this when stable/dynamic/LoRA/xDiT inference fails or produces a shape, memory, or checkpoint error.

## Missing Checkpoints

**Symptoms**

- `ValueError: \`models_root\` not exists`
- `No model weights found`
- `AssertionError: VAE checkpoint not found`

**Fix**

- Read [`../../../references/checkpoints.md`](../../../references/checkpoints.md).
- From the real checkout root, run `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference`.
- Download the missing transformer, VAE, or text-encoder tree before retrying; do not create placeholder weights.

## Memory / Resolution Problems

**Symptoms**

- CUDA OOM
- very slow inference on a small GPU
- the README’s 720p recipe does not fit the host

**Fix**

- Use `--use-cpu-offload`.
- Drop to `--i2v-resolution 540p` or `360p` if the host cannot fit the larger configuration.
- Reduce the number of parallel GPUs if xDiT is making the setup more expensive than necessary.

## xDiT / Sequence-Parallel Errors

**Symptoms**

- `number of GPUs should be equal to ring_degree * ulysses_degree`
- image size is not divisible by the sequence-parallel degree
- `xfuser` import error

**Fix**

- Make the degree product equal to the active GPU count.
- If you accept the resize, set `ALLOW_RESIZE_FOR_SP=1` before running.
- Install `xfuser==0.4.0` only when the multi-GPU route is required.

## LoRA Inference Errors

**Symptoms**

- missing `.safetensors` file
- LoRA command runs but no effect is visible
- shape mismatch when loading weights

**Fix**

- Check that `--use-lora` and `--lora-path` are both set.
- Verify the LoRA file belongs to this repo’s weight format.
- Confirm the base checkpoint tree is complete before applying the adapter.

## Prompt / Input Validation Errors

**Symptoms**

- prompt is not a string
- invalid `i2v_resolution` or `i2v_condition_type`
- invalid `video_length`
- unexpected crop or resize at I2V preprocessing time

**Fix**

- Use a plain string prompt.
- Keep `i2v_resolution` within `360p`, `540p`, `720p`.
- Keep `video_length - 1` divisible by 4.
- Prefer concise prompts; the README explicitly advises short, structured descriptions.

## Debug Order

Run from `$CHECKOUT_ROOT`; `$SKILL_ROOT` is the generated-skill directory:

1. `python "$SKILL_ROOT/scripts/check_runtime.py" --repo-root "$CHECKOUT_ROOT" --check-imports --check-decord --check-omegaconf`
2. `python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference`
3. `python "$SKILL_ROOT/sub-skills/inference/scripts/run_sample_image2video.py" --repo-root "$CHECKOUT_ROOT" --dry-run ...`
4. Execute only after the dry-run and checkpoint checks are clean.
